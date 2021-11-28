#!/bin/bash
REGISTRY=836736564967.dkr.ecr.us-east-2.amazonaws.com/tbp-postgres
REGION=us-east-2

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $REGISTRY

if [ -z "$1" ]
  then
    docker-compose up
  else
    docker-compose run web "$@"
fi
