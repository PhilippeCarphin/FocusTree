#!/bin/bash

npm run build

cp ~/Dropbox/Notes/Notes_BUCKET/Notes_FocusTree.html help.html

rsync -av ./build/ apt-rpi:~/Documents/GitHub/FocusTree/clients/ft-web-client/build/
