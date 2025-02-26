#!/usr/bin/env bash
container_id=$(docker ps | grep mosquitto | cut -d " " -f 1)
if [ -n "$container_id" ]; then
    echo "Stopping mosquitto"
    docker stop \
	   $container_id > /dev/null
    echo "Removing mosquitto"
    docker rm \
	   $container_id > /dev/null
else
    echo "Mosquitto is not running"
fi
