mkdir -p mosquitto/config
mkdir -p mosquitto/data
mkdir -p mosquitto/log
docker run -it -d --name mosquitto \
       -p 1883:1883 \
       -v $PWD/mosquitto:/mosquitto eclipse-mosquitto:latest
