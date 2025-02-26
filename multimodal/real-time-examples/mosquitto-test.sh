#!/usr/bin/env bash
container_id=$(docker ps | grep mosquitto | cut -d " " -f 1)
if [ -n "$container_id" ]; then
    pushd paho-mqtt-examples
    python client_pub_opts.py -H localhost -u mosquitto -p $MOSQUITTO_PASSWD -P 1883
    popd
else
    echo "Mosquitto is not running"
fi
