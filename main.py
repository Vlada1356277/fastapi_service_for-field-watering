from contextlib import asynccontextmanager

import json
from typing import TypedDict

import uvicorn
from fastapi import FastAPI
import psycopg2
from src.backend.database import models
from src.backend.database.database import engine, SessionLocal
from src.backend.database.models import Device
from src.backend.mqtt_client import connect_mqtt
from src.backend.routers import subscribe_device, add_sensor, device_data
from fastapi.staticfiles import StaticFiles

from src.backend.routers.read_mqtt import State, on_message
from starlette.datastructures import State

models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = connect_mqtt()
    client.on_message = on_message
    # starts the background network thread
    client.loop_start()

    # подписка на все топики из бд
    # subscribe([("my/topic", 0), ("another/topic", 2)])
    db = SessionLocal()
    devices = db.query(Device).all()
    db.close()

    topics: list[tuple[str, int]] = []
    for device in devices:
        topics.append((f"+/{device.serial_number}", 2,))

    if topics:
        client.subscribe(topics)
    app.state.client = client

    print("subscribed to MQTT topic " + f"{topics}")

    yield

    client.loop_stop()
    client.disconnect()
    print("disconnected")


app = FastAPI(lifespan=lifespan)

app.include_router(subscribe_device.router)
app.include_router(add_sensor.router)
app.include_router(device_data.router)

# отрисовка html
app.mount("/templates", StaticFiles(directory="templates"), name="templates")


@app.get("/")
async def read_root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

#
# @app.post("/change_program")
# async def change_program(program_id: int):
#     # Logic to publish message to change program
#     mqtt_client.publish("change_program_topic", str(program_id))
#     return {"message": "Program changed successfully"}

# def process_message(topic, payload):
#     # Logic to process incoming messages from MQTT
#     pass
