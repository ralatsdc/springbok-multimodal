#!/usr/bin/env bash
container_id=$(docker ps | grep mosquitto | cut -d " " -f 1)
if [ -z "$container_id" ]; then
    mkdir -p mosquitto/config
    mkdir -p mosquitto/data
    mkdir -p mosquitto/log
    docker run \
	   -it \
	   -d \
	   --name mosquitto \
	   -p 1883:1883 \
	   -v $PWD/mosquitto:/mosquitto eclipse-mosquitto:latest
else
    echo "Mosquitto is already running"
fi
