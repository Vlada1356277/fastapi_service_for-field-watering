# чтение, сохранение в бд. Работа с json

import json
from typing import TypedDict, Dict

from src.backend.routers.device_data import devices_data, devices_types


# типизация структуры из mqtt
class Sensors(TypedDict):
    type: str
    uuid: str
    value: int
    lastTs: int


class Schedule:
    startTs: int
    endTs: int


class Output(TypedDict):
    name: str
    value: bool
    lastTs: int
    id: int
    uuidWirelessSensor: str
    schedule: dict


class WirelessSensor(TypedDict):
    rssi: int
    name: str
    lastTs: int
    uid: str
    batteryLevel: int
    humidity: int


class State(TypedDict):
    rssi: int
    temperature: int
    sensors: list[Sensors]
    outputs: list[Output]
    wirelessSensors: list[WirelessSensor]


def on_message(client, userdata, msg):
    # parse a valid JSON string and convert it into a Python Dictionary
    state: State = json.loads(msg.payload)
    print('-->', state)

    # данные главного устр-ва для отображения
    device_SN = extract_device_id_from_topic(msg.topic)
    devices_data[device_SN] = {
        "rssi": state['rssi'],
        "temperature": state['temperature']
    }
    print(f'Updated device {device_SN} data:', devices_data[device_SN])

    if device_SN not in devices_types:
        device_type = msg.topic.split('/')[0]
        devices_types[device_SN] = device_type
    print(devices_types)

def extract_device_id_from_topic(topic: str) -> str:
    # Extract device ID from topic
    return topic.split('/')[1]
