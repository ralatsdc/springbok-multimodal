docker run -it -d -p 1883:1883 --name mos \
       -v $PWD/mosquitto:/mosquitto eclipse-mosquitto:latest
