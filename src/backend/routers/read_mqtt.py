# чтение, сохранение в бд. Работа с json

import json
from typing import TypedDict, Dict

from src.backend.database.database import SessionLocal
from src.backend.database.models import SensorReading
from src.backend.database.schemas import State
from src.backend.routers.device_data import devices_data, devices_types, last_messages
from src.backend.database.models import WirelessSensor


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


class WirelessSensors(TypedDict):
    rssi: int
    name: str
    lastTs: int
    uid: str
    batteryLevel: int
    humidity: int


# class State(TypedDict):
#     rssi: int
#     temperature: int
#     sensors: list[Sensors]
#     outputs: list[Output]
#     wirelessSensors: list[WirelessSensors]


def on_message(client, userdata, msg):
    # parse a valid JSON string and convert it into a Python Dictionary
    try:
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
        print("Типы устройств для подписки: ", devices_types)

        # обработка данных датчика
        process_sensor_data(state['wirelessSensors'])

        last_messages[device_SN] = state

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error processing message: {e}")


def extract_device_id_from_topic(topic: str) -> str:
    # Extract device ID from topic
    return topic.split('/')[1]


def process_sensor_data(wireless_sensors):
    db = SessionLocal()
    try:
        for sensor_data in wireless_sensors:
            sensor_uid = sensor_data['uid']
            rssi = sensor_data['rssi']
            humidity = sensor_data['humidity']
            battery_level = sensor_data['batteryLevel']
            last_ts = sensor_data['lastTs']

            # Проверяем, существует ли сенсор в базе данных
            sensor = db.query(WirelessSensor).filter(WirelessSensor.uid == sensor_uid).first()
            # sensor = db.query(WirelessSensor).filter(WirelessSensor.uid == sensor_uid).first()
            if sensor:
                # Создаем новую запись с данными сенсора
                sensor_reading = SensorReading(
                    wireless_sensor_uid=sensor_uid,
                    rssi=rssi,
                    humidity=humidity,
                    battery_level=battery_level,
                    lastTs=last_ts
                )
                db.add(sensor_reading)
                db.commit()
                db.refresh(sensor_reading)
                print(f"Добавлены данные для {sensor_uid}")
            else:
                print(f"Датчик {sensor_uid} не найден в базе данных")
    except Exception as e:
        db.rollback()
        print(f"Error processing sensor data: {e}")
    finally:
        db.close()
