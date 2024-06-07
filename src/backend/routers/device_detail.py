from datetime import datetime
from fastapi import APIRouter, Request, HTTPException

from src.backend.database.database import SessionLocal
from src.backend.database.models import Device, LastReadings
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
        last_reading = db.query(LastReadings).filter(LastReadings.device_id == device.id).first()

        sensors_list = []
        outputs_list = []

        if last_reading:
            if 'wirelessSensors' in last_reading.data:
                sensors_data = last_reading.data['wirelessSensors']
                for sensor in sensors_data:
                    # Преобразование Unix timestamp в читаемую дату и время
                    last_ts_readable = datetime.utcfromtimestamp(sensor['lastTs']).strftime('%Y-%m-%d %H:%M:%S') \
                        if sensor['lastTs'] else None
                    sensor_info = {
                        "uid": sensor['uid'],
                        "name": sensor.get('name', 'Unknown'),
                        "last_rssi": f"{sensor['rssi']} dBm" if 'rssi' in sensor else None,
                        "last_humidity": f"{sensor['humidity']} %" if 'humidity' in sensor else None,
                        "last_battery_level": f"{sensor['batteryLevel']} %" if 'batteryLevel' in sensor else None,
                        "last_ts": last_ts_readable
                    }
                    sensors_list.append(sensor_info)

            if 'outputs' in last_reading.data:
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
