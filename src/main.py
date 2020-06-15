import os
os.environ['CV_IO_MAX_IMAGE_WIDTH'] = '5490'
os.environ['CV_IO_MAX_IMAGE_HEIGHT'] = '5490'
os.environ['CV_IO_MAX_IMAGE_PIXELS'] = pow(2, 40).__str__()
os.environ['OPENCV_IO_ENABLE_JASPER'] = 'True'

from datetime import datetime
import numpy as np
import cv2 as cv
import re


def log(msg):
    print('[{}] {}'.format(now(), msg))


def now():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def find_output_dir():
    try:
        return os.environ['OUTPUT_DIR']
    except KeyError:
        return os.path.join(os.getcwd(), "results")


def find_images_dir():
    try:
        return os.environ['IMAGE_DIR']
    except KeyError:
        return os.path.join(os.getcwd(), "images")


def find_sub_dir():
    return os.environ['SUBDIR']


def get_threshold():
    try:
        return float(os.environ['THRESHOLD_PERCENT'])
    except KeyError:
        return 0.6


def find_images_path(start_path):
    result = []
    pattern = re.compile(r'TCI[A-Za-z0-9_]*\.jp2')

    for root, dirs, files in os.walk(start_path):
        for filename in files:
            if pattern.search(filename) is not None:
                log('Find {}'.format(os.path.join(root, filename)))
                result.append(os.path.join(root, filename))

    return result


MAX_IMAGE_LENGTH = 10980


class ImageProcessor:
    final_result = None

    def __init__(self):
        self.result = None

    def get_image(self, img_path):
        return cv.imread(img_path)

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

        hsv = cv.cvtColor(src, cv.COLOR_BGR2HSV)

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
    empty_white_img = processor.create_empty_white_img(width, height)

    files = find_images_path(os.path.join(find_images_dir(), find_sub_dir()))

    # 경계값 설정
    # threshold = int(len(files) * get_threshold())
    # log('Threshold percent: {}'.format(get_threshold()))
    threshold = 3
    log('Threshold value: {}'.format(3))

    for file in files:
        dir_path, file_name = os.path.split(file)
        processor.merge_image(dir_path, file_name)

    processor.write_result_by_threshold(
        empty_white_img,
        os.path.join(find_output_dir(), 'result_{}_{}.jpg'.format(find_sub_dir(), now())),
        threshold)


main()
