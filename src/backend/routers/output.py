# TOPIC: <device_type>/<master_uuid>/updated
import json
import time
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.backend.database.database import SessionLocal
from src.backend.database.models import Device, WirelessSensor, Output, LastReadings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# добавление и изменение выхода
@router.get("/devices/{device_SN}/output", response_class=HTMLResponse)
async def get_add_output_form(request: Request, device_SN: str):
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        sensors = db.query(WirelessSensor).filter(WirelessSensor.device_id == device.id).all()
        return templates.TemplateResponse("output.html", {
            "request": request,
            "device_SN": device_SN,
            "sensors": sensors
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# async def get_output_form(request: Request, device_SN: str):
#     return templates.TemplateResponse("output.html", {"request": request, "device_SN": device_SN})


@router.post("/devices/{device_SN}/output")
async def add_change_output(
        device_SN: str, sensor_uid: str = Form(...),
        output_id: int = Form(...), name: str = Form(...),
        start_ts: str = Form(...), end_ts: str = Form(...),
):
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        last_reading = db.query(LastReadings).filter(LastReadings.device_id == device.id).first()
        if not last_reading or 'outputs' not in last_reading.data:
            raise HTTPException(status_code=404, detail="Device data not found")

        last_message = last_reading.data

        start_ts_unix = parse_time_to_unix(start_ts)
        end_ts_unix = parse_time_to_unix(end_ts)

        output = {
            "name": name,
            "value": False,
            "lastTs": int(time.time()),
            "id": output_id,
            "uuidWirelessSensor": sensor_uid,
            "schedule": {
                "startTs": start_ts_unix,
                "endTs": end_ts_unix
            }
        }

        updated_state = last_message.copy()
        updated_state['outputs'].append(output)
        payload = json.dumps(updated_state, ensure_ascii=False)

        device_type = device.device_type

        # Формирование топика для отправки сообщения
        topic = f'{device_type}/{device_SN}/updated'

        from main import app

        client = app.state.client
        if not client:
            raise HTTPException(status_code=500, detail="MQTT client is not available")

        result = client.publish(topic, payload, qos=2)
        if result.rc != 0:
            raise HTTPException(status_code=500, detail="Failed to send MQTT message")

        # сохранение или обновление в БД
        try:
            existing_output = db.query(Output).filter(
                Output.id == output_id,
                Output.wireless_sensor_uid == sensor_uid
            ).first()

            if existing_output:
                # обновление существующего
                existing_output.name = name
                existing_output.value = False
                existing_output.startTime = start_ts_unix
                existing_output.endTime = end_ts_unix
                existing_output.lastTime = int(time.time())
            else:
                # добавление нового выхода
                new_output = Output(
                    name=name,
                    id=output_id,
                    startTime=start_ts_unix,
                    endTime=end_ts_unix,
                    lastTime=int(time.time()),
                    wireless_sensor_uid=sensor_uid
                )
                db.add(new_output)

            db.commit()
            if existing_output:
                db.refresh(existing_output)
            else:
                db.refresh(new_output)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save output to database") from e
        finally:
            db.close()

        return {"message": f"Output {output_id} updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def parse_time_to_unix(time_str):
    # извлечение current времени
    current_date = datetime.now().date()
    # преобразование времени
    time_obj = datetime.strptime(time_str, "%H:%M").time()
    # combines the current_date and time_obj into a single datetime object
    combined_datetime = datetime.combine(current_date, time_obj)
    return int(combined_datetime.timestamp())
