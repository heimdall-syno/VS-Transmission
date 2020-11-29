#!/bin/bash

## Check for sudo rights
if [ "$EUID" -ne 0 ]
  then printf "Please rerun as root:\n \$ sudo ./autogen.sh\n"
  exit
fi

## Host - Install pip for python3 and all needed modules
curl https://bootstrap.pypa.io/get-pip.py -o /get-pip.py
python3 /get-pip.py && rm -rf /get-pip.py
export PATH=$PATH:/volume1/@appstore/py3k/usr/local/bin
pip3 install -r requirements.txt

## Container - Install python3 and pip and all needed modules
containername=`docker ps | grep -i transmission | awk '{print $NF}'`
docker exec -it "$containername" apk add python3 ffmpeg
docker exec -it "$containername" curl https://bootstrap.pypa.io/get-pip.py -o /get-pip.py
docker exec -it "$containername" python3 /get-pip.py &&  rm -rf /get-pip.py
docker exec -it "$containername" pip3 install configparser
