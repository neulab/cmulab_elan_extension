#!/bin/bash
#
# It seems that recognizer processes invoked by ELAN don't inherit any regular
# environmental variables (like PATH), which makes it difficult to track down
# where both Python and ffmpeg(1) might be.  These same processes also have
# their locale set to C.  This implies a default ASCII file encoding.

export LC_ALL="en_US.UTF-8"
export PYTHONIOENCODING="utf-8"

# change to cmulab_elan_extension dir
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "PROGRESS: 1% (Initial setup) Creating virtual env, installing dependencies"
    python3 -m venv venv
    source venv/bin/activate
    python3 -m pip --no-input install -r requirements.txt
    echo "PROGRESS: 5% One-time initialization successfully completed!"
    deactivate
fi

source venv/bin/activate
python3 ./cmulab_elan_extension.py
