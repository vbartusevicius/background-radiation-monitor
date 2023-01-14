import time
import os
import datetime
import RPi.GPIO as GPIO
import paho.mqtt.publish as publish
from collections import deque

counts = deque()

usvh_ratio = float(os.getenv('TUBE_USVH_RATIO', default = 0.00812037037037)) # This is for the J305 tube
gpio_port = int(os.getenv('GPIO_PORT', default = 7))
mqtt_host = os.getenv('MQTT_HOST')
mqtt_port = int(os.getenv('MQTT_PORT', 1883))
mqtt_user = os.getenv('MQTT_USER')
mqtt_pass = os.getenv('MQTT_PASS')
mqtt_topic_prefix = os.getenv('MQTT_TOPIC_PREFIX')

# This method fires on edge detection (the pulse from the counter board)
def countme(channel):
    global counts
    timestamp = datetime.datetime.now()
    counts.append(timestamp)


# Set the input with falling edge detection for geiger counter pulses
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(gpio_port, GPIO.IN)
GPIO.add_event_detect(gpio_port, GPIO.FALLING, callback=countme)
loop_count = 0

# In order to calculate CPM we need to store a rolling count of events in the last 60 seconds
# This loop runs every second and removes elements from the queue that are older than 60 seconds
while True:
    loop_count = loop_count + 1

    try:
        while counts[0] < datetime.datetime.now() - datetime.timedelta(seconds=60):
            counts.popleft()
    except IndexError:
        pass # there are no records in the queue.

    if loop_count == 10:
        # Every 10th iteration (10 seconds), store a measurement in Influx

        data = [
            {
                'topic': "{prefix}/radiation/cpm".format(prefix=mqtt_topic_prefix),
                'payload': int(len(counts))
            },
            {
                'topic': "{prefix}/radiation/usvh".format(prefix=mqtt_topic_prefix),
                'payload': "{:.2f}".format(len(counts) * usvh_ratio)
            }
        ]

        publish.multiple(data, hostname=mqtt_host, port=mqtt_port, auth={'username':mqtt_user, 'password':mqtt_pass})
        loop_count = 0

    time.sleep(1)

