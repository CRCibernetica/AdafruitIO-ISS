# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
import time
from random import randint
import adafruit_requests as requests

import ssl
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT
import json

import board
from ideaboard import IdeaBoard

ib = IdeaBoard()

### WiFi ###

# Add a secrets.py to your filesystem that has a dictionary called secrets with "ssid" and
# "password" keys with your WiFi credentials. DO NOT share that file or commit it into Git or other
# source control.
# pylint: disable=no-name-in-module,wrong-import-order
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Set your Adafruit IO Username and Key in secrets.py
# (visit io.adafruit.com if you need to create an account,
# or if you need your Adafruit IO key.)
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])

# Define callback functions which will be called when certain events happen.
# pylint: disable=unused-argument
def connected(client):
    # Connected function will be called when the client is connected to Adafruit IO.
    # This is a good place to subscribe to feed changes.  The client parameter
    # passed to this function is the Adafruit IO MQTT client so you can make
    # calls against it easily.
    print("Connected to Adafruit IO!  Listening for DemoFeed changes...")
    # Subscribe to changes on a feed named DemoFeed.
    client.subscribe("control")


def subscribe(client, userdata, topic, granted_qos):
    # This method is called when the client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(client, userdata, topic, pid):
    # This method is called when the client unsubscribes from a feed.
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))


# pylint: disable=unused-argument
def disconnected(client):
    # Disconnected function will be called when the client disconnects.
    print("Disconnected from Adafruit IO!")


# pylint: disable=unused-argument
def message(client, feed_id, payload):
    # Message function will be called when a subscribed feed has a new value.
    # The feed_id parameter identifies the feed, and the payload parameter has
    # the new value.
    print("Feed {0} received new value: {1}".format(feed_id, payload))
    if feed_id == "control":
        if payload == "ON":
            ib.pixel = (0,0,255)
        elif payload == "OFF":
            ib.pixel = (0,0,0)
        else:
            ib.arcoiris = int(payload)

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)
https = requests.Session(pool, ssl.create_default_context())

# Initialize a new MQTT Client object
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    port=1883,
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)

# Connect the callback methods defined above to Adafruit IO
io.on_connect = connected
io.on_disconnect = disconnected
io.on_subscribe = subscribe
io.on_unsubscribe = unsubscribe
io.on_message = message

# Connect to Adafruit IO
print("Connecting to Adafruit IO...")
io.connect()

# Below is an example of manually publishing a new  value to Adafruit IO.
last = 0
print("Publishing a new message every 10 seconds...")
while True:
    # Explicitly pump the message loop.
    io.loop()
    # Send a new message every 10 seconds.
    if (time.monotonic() - last) >= 10:
        URL = "http://api.open-notify.org/iss-now.json"
        data = https.get(URL).json()
        long = data['iss_position']['longitude']
        lat = data['iss_position']['latitude']
        payload = {
                   "value": 22.5, 
                   "lat": lat,
                   "lon": long, 
                   "ele": 100
                    }
        payload = json.dumps(payload)
        print("Publishing {0} to datos.".format(payload))
        io.publish("datos", payload)
        last = time.monotonic()