import os
os.environ['CV_IO_MAX_IMAGE_PIXELS'] = pow(2, 40).__str__()

'''
OPENCV_IO_ENABLE_JASPER 환경 설정

True일 때 RGB 데이터를 HSV 형식으로 바꿀 수 있습니다.
'''
os.environ['OPENCV_IO_ENABLE_JASPER'] = 'True'

from datetime import datetime
import numpy as np
import cv2 as cv
import re


'''
log 함수는 로깅을 도와주는 유틸리티 함수 입니다.
'''
def log(msg):
    print('[{}] {}'.format(now(), msg))


'''
now 함수는 현재 시간을 계산해줍니다.
'''
def now():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


'''
find_output_dir 함수는 결과물을 저장할 위치를 설정합니다.

기본적으로 opencv-project/results 폴더에 결과를 저장하고 OUTPUT_DIR 환경 변수를 통해서
저장 경로를 바꿀 수 있습니다.
'''
def find_output_dir():
    try:
        return os.environ['OUTPUT_DIR']
    except KeyError:
        return os.path.join(os.getcwd(), "results")

'''
find_images_dir 함수는 이미지를 불러올 루트 경로를 설정합니다.

기본적으로 opencv-project/images 폴더에 결과를 저장하고 IMAGE_DIR 환경 변수를 통해서
저장 경로를 바꿀 수 있습니다.
'''
def find_images_dir():
    try:
        return os.environ['IMAGE_DIR']
    except KeyError:
        return os.path.join(os.getcwd(), "images")


'''
find_sub_dir 함수는 특정 대상지역의 이미지를 불러오기 위한 서브 디렉토리를 설정합니다.

예를 들어

opencv-project/images/yeong-am에 영암군 지역의 이미지들이 들어있다면,

  IMAGE_DIR은 images가 되고 SUBDIR은 yeong-am이 됩니다.
'''
def find_sub_dir():
    return os.environ['SUBDIR']


'''
get_threshold 함수는 경계값 설정을 도와줍니다.
'''
def get_threshold():
    try:
        return float(os.environ['THRESHOLD_PERCENT'])
    except KeyError:
        return 0.6


'''
find_images_path 함수는 재귀적으로 디렉토리 하부에 있는 센티넬 이미지들 중

r'TCI[A-Za-z0-9_]*\.jp2' 정규식을 만족하는 파일들을 찾아냅니다.

예를 들어

.
├── Cargo.toml
└── images
    └── yeong-am
        ├── sub1
        │   └── foo.TCI.jp2       
        └── sub2
            └── bar.TCI.jp2

와 같은 디렉토리 구조가 있을 때 find_images_path('images')와 같이 호출한다면
images/yeong-am/sub1/foo.TCI.jp2, images/yeong-am/sub2/bar.TCI.jp2 를 반환합니다. 

'''
def find_images_path(start_path):
    result = []
    pattern = re.compile(r'TCI[A-Za-z0-9_]*\.jp2')

    for root, dirs, files in os.walk(start_path):
        for filename in files:
            if pattern.search(filename) is not None:
                log('Find {}'.format(os.path.join(root, filename)))
                result.append(os.path.join(root, filename))

    return result

'''
MAX_IMAGE_LENGTH 상수는 센티넬로부터 제공되는 TCI 이미지 중 어떤 크기의 사진을 추출할 것인지를 결정합니다.

MAX_IMAGE_LENGTH는 이미지의 한변의 픽셀 수를 나타냅니다.
'''
MAX_IMAGE_LENGTH = 10980


'''
ImageProcessor는 이미지를 가공하고 출력하는 역할을 수행합니다.
'''
class ImageProcessor:
    final_result = None

    def __init__(self):
        self.result = None

    '''
    get_image 함수는 특정 경로에 존재하는 이미지를 읽어들이고 RGB 데이터의 매트릭스를 반환합니다.
    '''
    def get_image(self, img_path):
        return cv.imread(img_path)


    '''
    merge_image 함수는 dir_path, file_name에 존재하는 이미지를 읽어들여 HSV로 변환 후 초록색 경계값에
    있는 픽셀들을 추출하여 final_result에 합연산을 통해 병합시킵니다.
    '''
    def merge_image(self, dir_path, file_name):
        GREEN_LOW = (36, 0, 0)
        GREEN_HIGH = (86, 255, 255)

        img_path = os.path.join(dir_path, file_name)
        src = self.get_image(img_path)
        if src is None:
            raise FileNotFoundError(img_path)

        height, width, _ = src.shape
        log('height: {}, width: {}'.format(height, width))
        if height != MAX_IMAGE_LENGTH:
            return

        # RGB 데이터를 HSV로 변환합니다.
        hsv = cv.cvtColor(src, cv.COLOR_BGR2HSV)

        # HSV의 데이터 중 GREEN_LOW, GREEN_HIGH 사이에 존재하는 픽셀들을 추출합니다.
        mask = cv.inRange(hsv, GREEN_LOW, GREEN_HIGH)
        green_mask = (mask > 0).astype(int)
        if self.final_result is None:
            self.final_result = green_mask
        else:
            self.final_result += green_mask

        log('merged successfully: {}'.format(os.path.join(dir_path, file_name)))

    def get_result_by_threshold(self, threshold):
        result = self.final_result >= threshold
        return result

    def write_result_by_threshold(self, sample, output_path, threshold):
        white_background = (255, 255, 255)
        mask = self.get_result_by_threshold(threshold)

        img = np.zeros_like(sample, np.uint8)
        img[mask] = [0, 0, 0]
        img[mask == 0] = white_background

        log(output_path)
        cv.imwrite(output_path, img)

    def create_empty_white_img(self, width, height):
        result = np.zeros((height, width, 3), np.uint8)
        result.fill(255)
        return result


def main():
    processor = ImageProcessor()
    width = MAX_IMAGE_LENGTH
    height = MAX_IMAGE_LENGTH

    # 결과물의 가장 기본이 되는 흰바탕의 이미지를 만듭니다.
    empty_white_img = processor.create_empty_white_img(width, height)

    # 대상지역의 센티넬 이미지를 모두 불러옵니다.
    files = find_images_path(os.path.join(find_images_dir(), find_sub_dir()))

    # 경계값 설정
    threshold = int(len(files) * get_threshold())
    log('Threshold percent: {}'.format(get_threshold()))
    log('Threshold value: {}'.format(threshold))

    # 대상 지역의 이미지들을 병합시킵니다.
    for file in files:
        dir_path, file_name = os.path.split(file)
        processor.merge_image(dir_path, file_name)

    # 병합된 이미지에 대해 특정 경계값 이상의 데이터만을 추출하여 흰바탕의 이미지에 씁니다.
    processor.write_result_by_threshold(
        empty_white_img,
        os.path.join(find_output_dir(), 'result_{}_{}.jpg'.format(find_sub_dir(), now())),
        threshold)


main()
