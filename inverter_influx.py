from inverter_config import influx as influxConfig

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

class InverterInflux:
    def __init__(self, logger):        
        self.logger = logger

        self.enabled = influxConfig["enabled"]
        token = influxConfig["token"]
        org = influxConfig["org"]
        bucket = influxConfig["bucket"]
        url = influxConfig["url"]
        write_client = InfluxDBClient(url=url, token=token, org=org)

        self.org=org
        self.bucket=bucket
        self.write_api = write_client.write_api(write_options=SYNCHRONOUS)

    def upload_qpigs(self, timestamp, data):
        if self.enabled:
            self.logger.debug(f'InfluxDB upload qpigs at {timestamp} data {data}') 
            point = (
                Point("inverter")
                .field("batteryVoltage", data["batteryVoltage"])
                .field("batteryCurrent", data["batteryCurrent"])
                .field("outputLoadPercent", data["outputLoadPercent"])
                .field("outputApparentPower", data["outputApparentPower"])
                .field("outputActivePower", data["outputActivePower"])
                .field("temperature", data["temperature"])
                .time(int(timestamp.timestamp()), WritePrecision.S)
            )
           
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
