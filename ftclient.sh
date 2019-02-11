#!/bin/bash

cd $(dirname $(python -c "import os,sys; print(os.path.realpath(sys.argv[1]))" ${BASH_SOURCE[0]}))

my_ip=$(curl ipinfo.io/ip 2>/dev/null)
if [[ $my_ip == 96.21.220.140 ]] ; then
    apt_rpi=192.168.0.114
else
    apt_rpi=96.21.220.140
fi

port=4051
echo "Connecting to $apt_rpi on port $port"
python3 ftclient.py --port $port --host $apt_rpi
