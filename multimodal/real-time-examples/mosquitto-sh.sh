#!/usr/bin/env bash
container_id=$(docker ps | grep mosquitto | cut -d " " -f 1)
if [ -n "$container_id" ]; then
    docker exec -it  -u 1883 mosquitto sh
else
    echo "Mosquitto is not running"
fi
