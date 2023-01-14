FROM python:3.7

WORKDIR /usr/app/src
RUN pip install RPi.GPIO paho-mqtt
COPY src/counter.py ./

CMD ["python","counter.py"]
