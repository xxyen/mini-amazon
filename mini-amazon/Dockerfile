FROM python:3.8.10
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ADD . /code/
RUN chmod +x ./install.sh
RUN chmod +x .flaskenv
# RUN poetry run ./install.sh