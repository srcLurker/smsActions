#!/bin/bash
CONFIG_DIRECTORY=~/src/smsActions/config

docker stop dsms
docker rm dsms

# port 8321 is used by the python server to listen
# for sms notifcation. Pass that port through so
# nginx knows where to send the info.
docker run \
  --name dsms \
  --user 1001:1001 \
  --publish 8321:8321 \
  -v ${CONFIG_DIRECTORY}:/opt/external \
  --entrypoint=/bin/bash \
  -it \
  docker_sms
