from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, CheckConstraint, JSON, DateTime
from sqlalchemy.orm import relationship

from .database import Base


class Device(Base):
    __tablename__: str = 'devices'

    id = Column(Integer, primary_key=True)
    serial_number = Column(String, unique=True)
    device_type = Column(String, nullable=True)
    name = Column(String, nullable=True)

    # Связь один ко многим с WirelessSensor
    wireless_sensors = relationship('WirelessSensor', back_populates='device')


class WirelessSensor(Base):
    __tablename__ = 'wireless_sensors'

    uid = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True)

    device_id = Column(Integer, ForeignKey('devices.id', ondelete="CASCADE"), nullable=False)

    readings = relationship("SensorReading", back_populates="sensor")

    # Связь один ко многим с Output
    output = relationship("Output", back_populates="wireless_sensor")

    # Обратная связь с Device
    device = relationship("Device", back_populates="wireless_sensors")


class SensorReading(Base):
    __tablename__ = 'sensor_reading'
    id = Column(Integer, primary_key=True, index=True)
    wireless_sensor_uid = Column(String, ForeignKey('wireless_sensors.uid', ondelete="CASCADE"))
    humidity = Column(Integer, nullable=True)
    battery_level = Column(Integer, nullable=True)
    rssi = Column(Integer, nullable=True)
    lastTs = Column(Integer, nullable=True)

    sensor = relationship("WirelessSensor", back_populates="readings")


class Output(Base):
    __tablename__ = 'outputs'

    global_id = Column(Integer, primary_key=True, index=True)
    id = Column(Integer, nullable=False)

    name = Column(String, nullable=True)
    # value = Column(Boolean, nullable=False)
    startTime = Column(Integer, nullable=False)
    endTime = Column(Integer, nullable=True)
    lastTime = Column(Integer, nullable=True)

    # Adding a constraint to ensure id is between 1 and 4
    __table_args__ = (
        CheckConstraint('id >= 1 AND id <= 4', name='id_range_constraint'),
    )

    wireless_sensor_uid = Column(String, ForeignKey('wireless_sensors.uid', ondelete='CASCADE'), nullable=False)

    # Обратная связь с WirelessSensor
    wireless_sensor = relationship("WirelessSensor", back_populates="output")


class LastReadings(Base):
    __tablename__ = 'last_readings'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete="CASCADE"), nullable=False)
    data = Column(JSON)
