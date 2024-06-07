from fastapi import HTTPException, APIRouter

from src.backend.mqtt_client import subscribe_mqtt
from src.backend.database import schemas
from src.backend.database.database import SessionLocal
from src.backend.database.models import Device
from src.backend.routers.read_mqtt import on_message
from sqlalchemy.exc import IntegrityError

router = APIRouter()


# подписка на топик в первый раз (запрос от Django)
@router.post("/subscribe_mqtt")
async def subscribe(data: schemas.DeviceData):
    serial_number = data.serial_number
    name = data.name
    topic = f"+/{serial_number}"

    # сохранение в БД
    db = SessionLocal()
    device = Device(serial_number=serial_number, name=name)

    try:
        db.add(device)
        db.commit()
        db.refresh(device)
    except IntegrityError as e:
        db.rollback()
        db.close()
        raise HTTPException(status_code=400, detail="Устройство уже существует") from e
    finally:
        db.close()

    # Подписка на MQTT topic с использованием полученных данных
    await subscribe_mqtt(topic)

    print("subscribed to MQTT topic " + f"{topic}")

    return {"message": "Subscribed to MQTT topic" + f"{topic}"}
