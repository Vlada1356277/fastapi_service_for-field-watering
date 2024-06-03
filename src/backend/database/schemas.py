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


class State(BaseModel):
    rssi: int
    temperature: int
    sensors: List[Dict]
    outputs: List[Dict]
    wirelessSensors: List[WirelessSensor]


class DeviceData(BaseModel):
    serial_number: str
    name: str


class AddOutputRequest(BaseModel):
    startTs: int
    endTs: int


class WirelessSensorBase(BaseModel):
    name: str
    device_id: int


class SensorsList(BaseModel):
    uid: str
    name: Optional[str]
    last_rssi: Optional[int]
    last_humidity: Optional[float]
    last_battery_level: Optional[int]
    last_ts: Optional[datetime]

    class Config:
        orm_mode = True


class WirelessSensorCreate(WirelessSensorBase):
    pass


class WirelessSensor(WirelessSensorBase):
    uid: int

    class Config:
        orm_mode = True


class OutputBase(BaseModel):
    wireless_sensor_uid: int
    value: bool
    startTime: int
    endTime: int
    lastTime: int


class OutputCreate(OutputBase):
    pass


class Output(OutputBase):
    id: int

    class Config:
        orm_mode = True
