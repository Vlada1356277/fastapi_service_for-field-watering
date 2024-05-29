import os

import paho.mqtt.client as mqtt
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Глобальная переменная для mqtt клиента
mqtt_client: None | mqtt.Client

# mqtt_broker_address = "test.mosquitto.org"
# port = 1883
broker = os.getenv('BROKER')
port = int(os.getenv('PORT', 1883))


def connect_mqtt():
    global mqtt_client
    mqtt_client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            return {"message": "Connected to MQTT Broker!" + f"{broker}"}
        else:
            print(f"Failed to connect, return code {rc}\n")

    # callback
    mqtt_client.on_connect = on_connect
    # mqtt_client.username_pw_set('username', 'password')
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



# def connect_mqtt():
#     client = mqtt.Client()
#
#     def on_connect(client, userdata, flags, rc):
#         if rc == 0:
#             print("Connected to MQTT Broker!")
#         else:
#             print(f"Failed to connect, return code {rc}\n")
#
#     # callback
#     client.on_connect = on_connect
#     # client.username_pw_set('username', 'password')
#     client.connect(broker, port)
#     return client


# def subscribe_mqtt(dt, sn):
#     client = mqtt.Client()
#     mqtt_client


# class MQTTClient:
#     @staticmethod
#     def connect_mqtt() -> mqtt:
#         def on_connect(client, userdata, flags, rc, properties=None):
#             if rc == 0:
#                 print("Connected to MQTT Broker!")
#             else:
#                 print("Failed to connect, return code %d\n", rc)
#
#         client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
#         client.on_connect = on_connect
#         client.connect(broker, port)
#         return client
#
#     @staticmethod
#     def subscribe(client: mqtt):
#         def on_message(client, userdata, msg):
#             print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
#
#         client.subscribe(mqtt_topic)
#         client.on_message = on_message
#
#     @staticmethod
#     def loop_forever():
#         client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
#         # client = MQTTClient.connect_mqtt()
#         # MQTTClient.subscribe(client)
#         client.loop_forever()

# def run():
#     client = connect_mqtt()
#     subscribe(client)
#     client.loop_forever()

# if __name__ == '__main__':
#     run()
