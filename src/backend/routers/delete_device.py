from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.backend.database import Device
from src.backend.database.database import SessionLocal
from src.backend.mqtt_client import fast_mqtt

router = APIRouter()


class DeviceSN(BaseModel):
    serial_number: str


@router.delete("/delete_device")
async def delete_device(data: DeviceSN):
    db = SessionLocal()
    try:
        # Получение устройства из базы данных
        serial_number = data.serial_number
        device = db.query(Device).filter(Device.serial_number == serial_number).first()

        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        # device = db.query(Device).filter(Device.serial_number == serial_number).first()
        # if not device:
        #     raise HTTPException(status_code=404, detail="Устройство не найдено")
        # device_type = device.device_type
        # if not device_type:
        #     raise HTTPException(status_code=404, detail="Тип устройства не найден")

        # topic = f"{device_type}/{serial_number}"
        topic = f"+/{serial_number}"
        fast_mqtt.client.unsubscribe(topic)

        db.delete(device)
        db.commit()

        print(f'Устройство {serial_number} удалено, отписка от топика {topic}')
        return {"message": f"Device {serial_number} deleted and unsubscribed from {topic}"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting device: {str(e)}")
    finally:
        db.close()
