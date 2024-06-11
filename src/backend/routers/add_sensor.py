# TOPIC: <device_type>/<master_uuid>/add-wireless-sensor
# сообщение:
# {
#   "name":"lora1",
#   "uid":"543uri6546gr",
# }
#
import json

from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from src.backend.database.database import SessionLocal
from src.backend.database.models import WirelessSensor, Device
from src.backend.database.schemas import SensorData
from src.backend.mqtt_client import fast_mqtt

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/devices/{device_SN}/add_sensor", response_class=HTMLResponse)
async def serve_html(request: Request, device_SN: str):
    return templates.TemplateResponse("qr.html", {"request": request, "device_SN": device_SN})


@router.post("/devices/{device_SN}/add_sensor")
async def add_sensor(device_SN: str, data: SensorData, request: Request):
    db = SessionLocal()
    try:
        sensor_uid = data.qrCodeMessage
        sensor_name = data.sensorName

        print(f"Received QR code message: {sensor_uid}")
        print(f"Received device name: {sensor_name}")

        # Формирование данных сенсора для отправки
        sensor_data = {
            "name": sensor_name,
            "uid": sensor_uid
        }

        # Преобразование данных в JSON
        payload = json.dumps(sensor_data)

        # извлечение типа устройства для топика
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if not device:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
        device_type = device.device_type
        if not device_type:
            raise HTTPException(status_code=404, detail="Тип устройства не найден")

        # Формирование топика для отправки сообщения
        topic = f'{device_type}/{device_SN}/add-wireless-sensor'
        print(topic)

        # отправление на mqtt
        try:
            fast_mqtt.publish(topic, payload, qos=2)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        # добавление данных сенсора в БД
        sensor = WirelessSensor(uid=sensor_uid, name=sensor_name, device_id=device.id)
        try:
            db.add(sensor)
            db.commit()
            db.refresh(sensor)
        except IntegrityError as e:
            db.rollback()
            db.close()
            raise HTTPException(status_code=400, detail="Устройство уже существует") from e
        finally:
            db.close()
        print(f"Data {sensor_uid} and {sensor_name} sent successfully on topic {topic}")
        return {"message": f"Data {sensor_uid} {sensor_name} sent successfully on topic {topic}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
