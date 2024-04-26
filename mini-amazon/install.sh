#!/bin/bash

mypath=`realpath "$0"`
mybase=`dirname "$mypath"`
cd $mybase

SECRET=`tr -dc 'a-z0-9-_' < /dev/urandom | head -c50`
echo "FLASK_APP=amazon.py
FLASK_DEBUG=True
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=8080
SECRET_KEY='$SECRET'
DB_NAME=amazon
DB_USER=postgres
DB_PORT=5432
DB_HOST=localhost
DB_PASSWORD=123456" > .flaskenv

poetry config virtualenvs.in-project true
poetry install
db/setup.sh
