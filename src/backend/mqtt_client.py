import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Глобальная переменная для mqtt клиента
mqtt_client: None | mqtt.Client

# mqtt_broker_address = "test.mosquitto.org"
# port = 1883
broker = os.getenv('BROKER')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
port = int(os.getenv('PORT', 1883))


def connect_mqtt():
    global mqtt_client
    mqtt_client = mqtt.Client()
    print(broker)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            return {"message": "Connected to MQTT Broker!" + f"{broker}"}
        else:
            print(f"Failed to connect, return code {rc}\n")

    # callback
    mqtt_client.on_connect = on_connect
    if not broker == 'test.mosquitto.org':
        mqtt_client.username_pw_set(username, password)
    mqtt_client.connect(broker, port)
    return mqtt_client


async def subscribe_mqtt(topic):
    global mqtt_client
    if mqtt_client is not None:
        print(mqtt_client)
        mqtt_client.subscribe(topic)
        return {"message": "Subscribed to topic " + f'{topic}'}
    else:
        raise RuntimeError("MQTT client is not connected")