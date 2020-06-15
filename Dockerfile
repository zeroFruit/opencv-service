FROM python:3.7

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

# Add requirements.txt before rest of repo for caching
ADD ./requirements.txt .
RUN pip install -r ./requirements.txt

COPY src ./src

ENTRYPOINT ["python", "./src/main.py"]