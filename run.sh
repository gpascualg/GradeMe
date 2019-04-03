#!/bin/bash

DC=$(which docker-compose)

if [ $? -ne 0 ]
then
    echo "Please install docker-compose (https://docs.docker.com/compose/)"
    exit
fi

ROOT_PATH=$(pwd)/..
PORT=8080 TESTS=$ROOT_PATH/Tests DB=$ROOT_PATH/db INSTANCES=/tmp/instances $DC up --force-recreate
