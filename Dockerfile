FROM python:alpine3.16

RUN apk add \
	ffmpeg \
	build-base

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY app .

RUN pip install --no-cache-dir -r ./requirements.txt
