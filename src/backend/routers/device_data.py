from typing import Dict
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

from src.backend.database import Device, LastReadings
from src.backend.database.database import SessionLocal

# можно и в бд сохранять
# devices_types: Dict[str, str] = {}

router = APIRouter()


class DeviceState(BaseModel):
    rssi: str
    temperature: str


# последняя информация об устройстве (rssi, temperature)
@router.get("/{device_SN}", response_model=DeviceState)
async def get_device_state(device_SN: str):
    db = SessionLocal()
    try:
        # Find the corresponding device in the database
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        last_reading = db.query(LastReadings).filter(LastReadings.device_id == device.id).first()
        if not last_reading:
            raise HTTPException(status_code=404, detail="Device data not found")

        last_message = last_reading.data

        return DeviceState(
            rssi=f"{last_message['rssi']} dBm",
            temperature=f"{last_message['temperature']}°C"
        )
    finally:
        db.close()
