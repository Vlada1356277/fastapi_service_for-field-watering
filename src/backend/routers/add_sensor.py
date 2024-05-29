# TOPIC: <device_type>/<master_uuid>/add-wireless-sensor
# сообщение:
# {
#   "name":"lora1",
#   "uid":"543uri6546gr",
# }
#
import json

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
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

        from main import app
        client = app.state.client
        if not client:
            raise HTTPException(status_code=500, detail="MQTT client is not available")

        result = client.publish(topic, str(payload), qos=2)

        if result.rc == 0:
            print(f"Data {sensor_uid} and {sensor_name} sent successfully on topic {topic}")
            return {"message": f"Data {sensor_uid} and {sensor_name} sent successfully on topic {topic}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send sensor data")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
