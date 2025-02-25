pushd paho-mqtt-examples
python client_pub_opts.py -H localhost -u mosquitto -p $MOSQUITTO_PASSWD -P 1883
popd
