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
from src.backend.routers.device_data import devices_types

router = APIRouter()
templates = Jinja2Templates(directory="templates")

#
# @router.get("/devices/{device_SN}/add_sensor", response_class=HTMLResponse)
# async def serve_html(device_SN: str):
#     with open("templates/qr.html", "r") as file:
#         return HTMLResponse(content=file.read())
@router.get("/devices/{device_SN}/add_sensor", response_class=HTMLResponse)
async def serve_html(request: Request, device_SN: str):
    return templates.TemplateResponse("qr.html", {"request": request, "device_SN": device_SN})


class SensorData(BaseModel):
    qrCodeMessage: str
    sensorName: str


@router.post("/devices/{device_SN}/add_sensor")
async def add_sensor(device_SN: str, data: SensorData, request: Request):
    try:
        sensor_uid = data.qrCodeMessage
        sensor_name = data.sensorName

        # логика
        print(f"Received QR code message: {sensor_uid}")
        print(f"Received device name: {sensor_name}")

        # Формирование данных сенсора для отправки
        sensor_data = {
            "name": sensor_name,
            "uid": sensor_uid
        }

        # Преобразование данных в JSON
        payload = json.dumps(sensor_data)

        device_type = devices_types.get(device_SN)
        if device_type is None:
            print("Тип устройства не определен, дождитесь сообщения от устройства")
            raise HTTPException(status_code=500, detail="Тип устройства не определен, дождитесь сообщения от устройства")

        # Формирование топика для отправки сообщения
        topic = f'{device_type}/{device_SN}/add-wireless-sensor'
        print(topic)

        from main import app
        client = app.state.client
        if not client:
            raise HTTPException(status_code=500, detail="MQTT client is not available")

        result = client.publish(topic, str(payload), qos=2)

        if result.rc == 0:
            # добавление uid и name в базу данных
            db = SessionLocal()
            device = db.query(Device).filter(Device.serial_number == device_SN).first()
            if not device:
                raise HTTPException(status_code=404, detail="Устройство не найдено")
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
            return {"message": f"Data {sensor_uid} and {sensor_name} sent successfully on topic {topic}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send sensor data")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
