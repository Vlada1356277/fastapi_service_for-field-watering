from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from sqlalchemy.orm import Session

from src.backend.database import models
from src.backend.database.database import engine, SessionLocal
from src.backend.database.models import Device
from src.backend.mqtt_client import fast_mqtt, subscribe_mqtt
from src.backend.routers import (subscribe_device, add_sensor, device_data, delete_sensor, device_detail,
                                 output, output_on_off)
from fastapi.staticfiles import StaticFiles

models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await fast_mqtt.mqtt_startup()

    # Подписка на все топики из базы данных
    db: Session = SessionLocal()
    devices = db.query(Device).all()
    db.close()

    topics = [f"+/{device.serial_number}" for device in devices]

    for topic in topics:
        await subscribe_mqtt(topic)

    print("subscribed to MQTT topics", topics)

    yield

    await fast_mqtt.mqtt_shutdown()

app = FastAPI(lifespan=lifespan)

# post("/subscribe_mqtt") - приходит с django при добавлнии устройства
app.include_router(subscribe_device.router)

# post("/devices/{device_SN}/add_sensor") - добавление сенсора через mqtt
# get("/devices/{device_SN}/add_sensor") - отрисовка qr для добавления сенсора
app.include_router(add_sensor.router)

# delete("/devices/{device_SN}/{sensor_uid}") - удаление сенсора
app.include_router(delete_sensor.router)

# get("/{device_SN}") - получение последней информации о девайсе (rssi, temperature), используется в джанго
app.include_router(device_data.router)

# get("/devices/{device_SN}")
app.include_router(device_detail.router)

# @router.get("/devices/{device_SN}/output") - отрисовка формы добавления и изменения выхода
# @router.post("/devices/{device_SN}/output") - обработка добавления выхода
app.include_router(output.router)

# get("/devices/{device_SN}/{sensor_uid}/{value}") -- вкл выкл выхода, лучше post но для тестов в браузере get
app.include_router(output_on_off.router)

# отрисовка html
app.mount("/templates", StaticFiles(directory="templates"), name="templates")


@app.get("/")
async def read_root():
    return {"message": "FastAPI service"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

