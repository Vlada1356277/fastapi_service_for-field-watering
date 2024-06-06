# {
#   "uid":"543uri6546gr",
# }
# <device_type>/<master_uuid>/remove-wireless-sensor
import json
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from src.backend.database.database import SessionLocal
from src.backend.database.models import WirelessSensor, Device

router = APIRouter()


@router.delete("/devices/{device_SN}/{sensor_uid}/")
async def delete_sensor(device_SN: str, sensor_uid: str):
    db = SessionLocal()
    try:
        message = {
            "uid": sensor_uid,
        }

        payload = json.dumps(message)

        # поиск device_type
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if not device:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
        device_type = device.device_type
        if not device_type:
            raise HTTPException(status_code=404, detail="Тип устройства не найден")

        # device_type = devices_types.get(device_SN)
        # if device_type is None:
        #     raise HTTPException(status_code=404, detail="device type is None")

        # Формирование топика для отправки сообщения
        topic = f'{device_type}/{device_SN}/remove-wireless-sensor'

        from main import app

        client = app.state.client
        if not client:
            raise HTTPException(status_code=500, detail="MQTT client is not available")

        result = client.publish(topic, str(payload), qos=2)
        # result code == 0 - успешная публикация
        if result.rc == 0:
            try:
                # Получаем сенсор по его UID
                sensor = db.query(WirelessSensor).filter(WirelessSensor.uid == sensor_uid).first()
                if not sensor:
                    raise HTTPException(status_code=404, detail="Sensor not found")

                # # Удаляем все связанные данные с сенсором
                # db.query(SensorReading).filter(SensorReading.sensor_id == sensor.id).delete()
                # db.query(Output).filter(Output.sensor_id == sensor.id).delete()

                # Удаляем сенсор
                db.delete(sensor)
                db.commit()

                print(f"{sensor_uid} deleted successfully")
                return {"message": f"{sensor_uid} deleted successfully"}
            except IntegrityError as e:
                db.rollback()
                raise HTTPException(status_code=500, detail="Failed to delete sensor data from database") from e
            finally:
                db.close()
                print(f" {sensor_uid} deleted successfully")
                return {"message": f" {sensor_uid} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send mqtt message")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
