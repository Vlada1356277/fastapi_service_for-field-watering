import os
import json
from dotenv import load_dotenv, find_dotenv
from fastapi_mqtt import FastMQTT, MQTTConfig
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.backend.database.database import SessionLocal
from src.backend.database.models import SensorReading, Device, LastReadings
from src.backend.database.schemas import State
from src.backend.database.models import WirelessSensor

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


@fast_mqtt.on_message()
async def on_message(client, topic, payload, qos, properties):
    db = SessionLocal()
    try:
        state = json.loads(payload)
        print(f'from topic {topic}', '-->', state)

        # достаем device_SN из топика сообщения
        device_SN = extract_device_id_from_topic(topic)

        # сохранение или обновление device_type из нужного топика
        device_type = topic.split('/')[0]
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if device:
            if device.device_type != device_type:
                device.device_type = device_type
                db.commit()
        else:
            raise HTTPException(status_code=404, detail="device isn't found in DB")

        # обработка данных датчика
        await process_sensor_data(state['wirelessSensors'])

        # сохранение последних сообщений в БД
        await store_last_readings(db, device_SN, state)

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error processing message: {e}")
        db.rollback()
    finally:
        db.close()


def extract_device_id_from_topic(topic: str) -> str:
    # Extract device ID from topic
    return topic.split('/')[1]


async def process_sensor_data(wireless_sensors):
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


async def store_last_readings(db: Session, device_SN: str, state: State):
    try:
        # Find the corresponding device in the database
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if not device:
            print(f"Device {device_SN} not found in the database.")
            return

        # check if a record already exists for this device
        last_reading = db.query(LastReadings).filter(LastReadings.device_id == device.id).first()

        if last_reading:
            # обновление данных
            last_reading.data = state
        else:
            new_reading = LastReadings(device_id=device.id, data=state)
            db.add(new_reading)

        # Commit the transaction
        db.commit()

    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        db.rollback()  # Rollback in case of error
    except Exception as e:
        print(f"Unexpected error: {e}")
        db.rollback()  # Rollback in case of error
