#!/bin/bash

# The credentials are not in the container so the container
# can be shared. The code expects the credentials to
# be accessible from inside the container at /opt/external.
export DOCKER_CONTENT_TRUST=1
docker build -f Dockerfile_sms -t docker_sms .
