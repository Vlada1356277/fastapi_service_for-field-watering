from datetime import datetime
from typing import List

from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Request, HTTPException

from src.backend.database.database import SessionLocal
from src.backend.database.models import Device, WirelessSensor, SensorReading
from src.backend.database.schemas import SensorsList

router = APIRouter()


@router.get("/devices/{device_SN}")
async def all_sensors(request: Request, device_SN: str):
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        sensors = db.query(WirelessSensor).filter(WirelessSensor.device_id == device.id).all()
        sensors_list = []
        for sensor in sensors:
            # отсортировать результаты запроса по столбцу last_ts в порядке убывания
            last_reading = db.query(SensorReading).filter(SensorReading.wireless_sensor_uid == sensor.uid).order_by(
                SensorReading.lastTs.desc()).first()

            # Преобразование Unix timestamp в читаемую дату и время
            last_ts_readable = datetime.utcfromtimestamp(last_reading.lastTs).strftime(
                '%Y-%m-%d %H:%M:%S') if last_reading else None

            sensor_data = {
                "uid": sensor.uid,
                "name": sensor.name,
                "last_rssi": f"{last_reading.rssi} dBm" if last_reading else None,
                "last_humidity": f"{last_reading.humidity} %" if last_reading else None,
                "last_battery_level": f"{last_reading.battery_level} %" if last_reading else None,
                "last_ts": last_ts_readable
            }
            sensors_list.append(sensor_data)

        return sensors_list
        # return [SensorsList(uid=sensor.uid, name=sensor.name) for sensor in sensors]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()



