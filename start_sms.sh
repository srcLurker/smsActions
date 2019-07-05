#!/bin/bash
#
# Script to startup in the docker environment.
# Leave the config files outside of the container so it's esaier to change.
#

EXTERNAL=/opt/external

python3 main.py -v -c ${EXTERNAL}/config.txt
