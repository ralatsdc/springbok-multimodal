mkdir -p mosquitto/config
mkdir -p mosquitto/data
mkdir -p mosquitto/log
docker run -it -d -p 1883:1883 --name mos \
       -v $PWD/mosquitto:/mosquitto eclipse-mosquitto:latest
