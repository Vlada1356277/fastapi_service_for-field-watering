from pydantic import BaseModel


class DeviceData(BaseModel):
    serial_number: str
    name: str


class WirelessSensorBase(BaseModel):
    device_id: int
    humidity: int
    battery_level: int
    rssi: int
    lastTs: int


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
