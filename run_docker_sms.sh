#!/bin/bash

CONFIG_DIRECTORY=~/src/smsActions/config

# Clean up any old stuff lying around.
docker stop dsms
docker rm dsms

# Python code uses port 8321. We'll use it too so nginx
# can find us. Also exporting the config directory
# which has the python_credentials file with the
# hue bridge info.
docker run \
  --detach \
  --name dsms \
  --user 1001:1001 \
  --restart=always \
  --log-opt max-size=100m \
  --log-opt max-file=10 \
  --publish 8321:8321 \
  -v ${CONFIG_DIRECTORY}:/opt/external \
  docker_sms

