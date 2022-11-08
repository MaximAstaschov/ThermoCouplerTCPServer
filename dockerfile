#Deriving the latest base image
FROM python:3-buster

#Labels as key value pair
LABEL Maintainer="astaschov@uni.mainz.de"
Label build_date="07_11_22"

WORKDIR /usr/src/app

EXPOSE 5530

RUN pip3 install rpi.gpio board adafruit-blinka thermocouples_reference adafruit-circuitpython-ads1x15
RUN pip3 install --upgrade setuptools adafruit-python-shell 


COPY TelnetServer.py ./

CMD python3 TelnetServer.py --host "192.168.2.118" --port 5530
