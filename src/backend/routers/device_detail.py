from datetime import datetime
from fastapi import APIRouter, Request, HTTPException

from src.backend.database.database import SessionLocal
from src.backend.database.models import Device, WirelessSensor, SensorReading, LastReadings
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# список сенсоров и выходов устройства
@router.get("/devices/{device_SN}")
async def all_sensors(request: Request, device_SN: str):
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        sensors = db.query(WirelessSensor).filter(WirelessSensor.device_id == device.id).all()
        sensors_list = []
        for sensor in sensors:
            # отсортировать результаты запроса по столбцу last_ts в порядке убывания
            last_reading = db.query(SensorReading).filter(SensorReading.wireless_sensor_uid == sensor.uid).order_by(
                SensorReading.lastTs.desc()).first()

            # Преобразование Unix timestamp в читаемую дату и время
            if last_reading and last_reading.lastTs is not None:
                last_ts_readable = datetime.utcfromtimestamp(last_reading.lastTs).strftime('%Y-%m-%d %H:%M:%S')
            else:
                last_ts_readable = None

            sensor_data = {
                "uid": sensor.uid,
                "name": sensor.name,
                "last_rssi": f"{last_reading.rssi} dBm" if last_reading else None,
                "last_humidity": f"{last_reading.humidity} %" if last_reading else None,
                "last_battery_level": f"{last_reading.battery_level} %" if last_reading else None,
                "last_ts": last_ts_readable
            }
            sensors_list.append(sensor_data)

        outputs_list = []
        last_reading = db.query(LastReadings).filter(LastReadings.device_id == device.id).first()
        if last_reading and 'outputs' in last_reading.data:
            outputs = last_reading.data['outputs']
            for output in outputs:
                sensor_name = 'Unknown'
                for sens in sensors_list:
                    if sens['uid'] == output['uuidWirelessSensor']:
                        sensor_name = sens['name']
                        break
                output_data = {
                    "id": output['id'],
                    "name": output['name'],
                    "value": output['value'],
                    "last_ts": datetime.utcfromtimestamp(output['lastTs']).strftime('%Y-%m-%d %H:%M:%S')
                    if output['lastTs'] is not None else None,
                    "sensor": sensor_name
                }
                outputs_list.append(output_data)

        return templates.TemplateResponse("device_detail.html", {
            "request": request,
            "device_SN": device_SN,
            "sensors": sensors_list,
            "outputs": outputs_list
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
