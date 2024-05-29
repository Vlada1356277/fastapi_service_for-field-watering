from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .database import Base


class Device(Base):
    __tablename__: str = 'devices'

    id = Column(Integer, primary_key=True)
    serial_number = Column(String, unique=True)
    name = Column(String, nullable=True)

    # Связь один ко многим с WirelessSensor
    wireless_sensors = relationship('WirelessSensor', back_populates='device')


class WirelessSensor(Base):
    __tablename__ = 'wireless_sensors'

    uid = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True)
    humidity = Column(Integer, nullable=True)
    battery_level = Column(Integer, nullable=True)
    rssi = Column(Integer, nullable=True)
    lastTs = Column(Integer, nullable=True)

    device_id = Column(Integer, ForeignKey('devices.id', ondelete="CASCADE"), nullable=False)

    # Связь один ко многим с Output
    outputs = relationship("Output", back_populates="wireless_sensor")

    # Обратная связь с Device
    device = relationship("Device", back_populates="wireless_sensors")


class Output(Base):
    __tablename__ = 'outputs'

    id = Column(Integer, primary_key=True, index=True)
    value = Column(Boolean, nullable=False)
    startTime = Column(Integer, nullable=False)
    endTime = Column(Integer, nullable=True)
    lastTime = Column(Integer, nullable=True)

    wireless_sensor_uid = Column(String, ForeignKey('wireless_sensors.uid', ondelete='CASCADE'), nullable=False)
    # Обратная связь с WirelessSensor
    wireless_sensor = relationship("WirelessSensor", back_populates="outputs")
