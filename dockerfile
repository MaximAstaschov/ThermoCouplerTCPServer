#Deriving the latest base image
FROM python:latest


#Labels as key value pair
LABEL Maintainer="astaschov@uni.mainz.de"
Label build_date="07_11_22"

WORKDIR ./

COPY TelnetServer.py ./


#CMD instruction should be used to run the software
#contained by your image, along with any arguments.

CMD [ "python3", "./TelnetServer.py", "--host  "192.168.2.118"", "--port 5530"]
