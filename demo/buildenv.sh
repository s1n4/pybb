#!/bin/sh
ENV=.env

echo Creating virtual environment
virtualenv --no-site-packages $ENV

echo Installing PIP inside virtual environment
$ENV/bin/easy_install pip

echo Installing dependencies into virtual environment
$ENV/bin/pip install -r ./requirements.txt

echo Creating var directory
mkdir -p var
