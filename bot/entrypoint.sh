#!/usr/bin/env bash

# exit from script if error was raised.
set -e

error() {
    echo "$1" > /dev/stderr
    exit 0
}

# setting timezone
echo "export TZ=\"/usr/share/zoneinfo/Europe/Zurich\"" >>  ~/.bashrc 

# run the software
python3 ./main.py 
