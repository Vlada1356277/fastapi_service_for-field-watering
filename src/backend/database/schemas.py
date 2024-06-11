from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class WirelessSensor(BaseModel):
    rssi: int
    name: str
    lastTs: int
    uid: str
    batteryLevel: int
    humidity: int


# mqtt_client.py
class State(BaseModel):
    rssi: int
    temperature: int
    sensors: List[Dict]
    outputs: List[Dict]
    wirelessSensors: List[WirelessSensor]
    humidity: Optional[int]


# subscribe_device.py
class DeviceData(BaseModel):
    serial_number: str
    name: str


class DeviceState(BaseModel):
    rssi: str
    temperature: str

class SensorData(BaseModel):
    qrCodeMessage: str
    sensorName: str


class SensorsList(BaseModel):
    uid: str
    name: Optional[str]
    last_rssi: Optional[int]
    last_humidity: Optional[float]
    last_battery_level: Optional[int]
    last_ts: Optional[datetime]

    class Config:
        orm_mode = True

