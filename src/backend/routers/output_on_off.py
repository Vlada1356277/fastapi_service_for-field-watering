import json
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.backend.database import Device, LastReadings
from src.backend.database.database import SessionLocal
from src.backend.mqtt_client import fast_mqtt

router = APIRouter()


class OutputTurn(BaseModel):
    value: bool


# принудительное включение-выключеие выхода
@router.get("/devices/{device_SN}/{sensor_uid}/{value}")
async def update_device_output(device_SN: str, sensor_uid: str, value: bool):
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        last_reading = db.query(LastReadings).filter(LastReadings.device_id == device.id).first()
        if not last_reading or 'outputs' not in last_reading.data:
            raise HTTPException(status_code=404, detail="Device data not found")

        device_message = last_reading.data

        for output in device_message["outputs"]:
            if output["uuidWirelessSensor"] == sensor_uid:
                output["value"] = value
                output["lastTs"] = int(time.time())
                break
            else:
                raise ValueError("Output с указанным wireless_sensor_uid не найден")

        payload = json.dumps(device_message, ensure_ascii=False)
        device_type = device.device_type
        if not device_type:
            raise ValueError("Тип устройства не найден")

        topic = f'{device_type}/{device_SN}/updated'

        try:
            fast_mqtt.publish(topic, payload, qos=2)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        if value:
            return {"message": "Полив будет принудительно запущен"}
        else:
            return {"message": "Полив будет принудительно остановлен"}

    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
#
# templates = Jinja2Templates(directory="templates")
#
#
# @router.get("/devices/{deviceSN}/{sensorUID}/turn_output", response_class=HTMLResponse)
# async def read_item(request: Request, deviceSN: str, sensorUID: str):
#     return templates.TemplateResponse("turn_output.html",
#                                       {"request": request,
#                                        "deviceSN": deviceSN,
#                                        "sensorUID": sensorUID})
