# In-memory storage for device data
from typing import Dict

from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

devices_data: Dict[str, dict] = {}
devices_types: Dict[str, str] = {}

router = APIRouter()


class DeviceState(BaseModel):
    rssi: str
    temperature: str


@router.get("/{device_SN}", response_model=DeviceState)
async def get_device_state(device_SN: str):
    device = devices_data.get(device_SN)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceState(
        rssi=f"{device['rssi']} dBm",
        temperature=f"{device['temperature']} °C")
