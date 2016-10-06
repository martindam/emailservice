FROM python:2.7
MAINTAINER Martin Dam <martinslothdam@gmail.com>

RUN mkdir -p /var/app/
WORKDIR /var/app/

RUN groupadd -r celery && useradd -r -g celery celery

COPY requirements.txt /var/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY static /var/app/static
COPY micromailer /var/app/micromailer
COPY *.py /var/app/

USER celery
