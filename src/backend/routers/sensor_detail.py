from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
from fastapi.templating import Jinja2Templates

from src.backend.database import Device, LastReadings
from src.backend.database.database import SessionLocal

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# сенсор и выход сенсора подробнее
@router.get("/devices/{device_SN}/{sensor_id}")
async def sensor_detail(request: Request, device_SN: str, sensor_id: str):
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.serial_number == device_SN).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        last_reading = db.query(LastReadings).filter(LastReadings.device_id == device.id).first()

        sensor_info = None
        output_data = None

        if last_reading:
            if 'wirelessSensors' in last_reading.data:
                sensors_data = last_reading.data['wirelessSensors']
                for wireless_sensor in sensors_data:
                    if wireless_sensor['uid'] == sensor_id:
                        sensor = wireless_sensor
                        last_ts_readable = datetime.utcfromtimestamp(sensor['lastTs']).strftime('%Y-%m-%d %H:%M:%S') if \
                        sensor['lastTs'] else None
                        sensor_info = {
                            "uid": sensor['uid'],
                            "name": sensor.get('name', 'Unknown'),
                            "last_rssi": f"{sensor['rssi']} dBm" if 'rssi' in sensor else None,
                            "last_humidity": f"{sensor['humidity']} %" if 'humidity' in sensor else None,
                            "last_battery_level": f"{sensor['batteryLevel']} %" if 'batteryLevel' in sensor else None,
                            "last_ts": last_ts_readable
                        }
                        break

            if 'outputs' in last_reading.data:
                outputs = last_reading.data['outputs']
                for output in outputs:
                    if output['uuidWirelessSensor'] == sensor_id:
                        output_data = {
                            "id": output['id'],
                            "name": output['name'],
                            "value": output['value'],
                            "last_ts": datetime.utcfromtimestamp(output['lastTs']).strftime('%Y-%m-%d %H:%M:%S') if
                            output['lastTs'] is not None else None,
                            "start_ts": datetime.utcfromtimestamp(output['schedule']['startTs']).strftime(
                                '%Y-%m-%d %H:%M:%S') if output['schedule']['startTs'] is not None else None,
                            "end_ts": datetime.utcfromtimestamp(output['schedule']['endTs']).strftime(
                                '%Y-%m-%d %H:%M:%S') if output['schedule']['endTs'] is not None else None,
                        }
                        break
        if not sensor_info:
            raise HTTPException(status_code=404, detail="Sensor not found")

        return templates.TemplateResponse("sensor_detail.html", {
            "request": request,
            "device_SN": device_SN,
            "sensor_id": sensor_id,
            "sensor_info": sensor_info,
            "output_info": output_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
