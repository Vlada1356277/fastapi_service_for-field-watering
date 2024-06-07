import os
from dotenv import load_dotenv, find_dotenv

from fastapi_mqtt import FastMQTT, MQTTConfig

load_dotenv(find_dotenv())

broker = os.getenv('BROKER')
port = int(os.getenv('PORT', 1883))

if broker != 'test.mosquitto.org':
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
else:
    username = None
    password = None

mqtt_config = MQTTConfig(
    host=broker,
    port=port,
    username=username,
    password=password
)
fast_mqtt = FastMQTT(config=mqtt_config)


@fast_mqtt.on_connect()
def on_connect(client, flags, rc, properties):
    if rc == 0:
        print(f"Connected to MQTT Broker: {broker}")
    else:
        print(f"Failed to connect to MQTT Broker: {broker}, return code {rc}\n")


@fast_mqtt.on_disconnect()
def on_disconnect(client, packet, exc=None):
    print("Disconnected")


async def subscribe_mqtt(topic):
    fast_mqtt.client.subscribe(topic)


async def disconnect_mqtt():
    await fast_mqtt.mqtt_shutdown()
