# FROM python:3.8.10
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y python3.8 && apt-get install -y postgresql postgresql-contrib && apt-get -y install python3-pip libpq-dev python3-dev libcairo2-dev pkg-config
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN python3 -m pip install --upgrade pip
RUN pip install psycopg2
RUN pip install -r requirements.txt
ADD . /code/
RUN chmod +x ./install.sh
RUN chmod +x .flaskenv
# RUN poetry run ./install.sh