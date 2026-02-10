import datetime
import json
from os.path import abspath, dirname
import sqlite3
import time
from threading import Lock
from inverter_energy_statistics import InverterEnergyStatistics
import schedule
from inverter_mqtt import InverterMqtt

class InverterRemotePanel:
    def __init__(self, logger, inverterEnergyStatistics: InverterEnergyStatistics):
        self.logger = logger
        self.inverterMqtt : InverterMqtt = InverterMqtt(logger)
        self.inverterEnergyStatistics = inverterEnergyStatistics
        self._last_energy_output = None
        self._last_energy_output_lock = Lock()
    
    def __updateEnergyOutput(self):
        try:
            self.logger.debug('Inverter remote panel loop running ...')
            energyTotal = self.inverterEnergyStatistics.getEnergyToatal('Output')
            energyLast12Months = self.inverterEnergyStatistics.getEnergyLast12Months('Output')
            energyLast30Days = self.inverterEnergyStatistics.getEnergyLastDays('Output', 30)
            energyLast7Days = self.inverterEnergyStatistics.getEnergyLastDays('Output', 7)
            energyYesterday = self.inverterEnergyStatistics.getEnergyDay('Output', True)
            energyToday = self.inverterEnergyStatistics.getEnergyDay('Output', False)
            data =  {
                "total": energyTotal,
                "last12Months": energyLast12Months,
                "last30Days": energyLast30Days,
                "last7Days": energyLast7Days,
                "yesterday": energyYesterday,
                "today": energyToday,
                "timestamp": datetime.datetime.now().isoformat()[:-3]
            }
            jsonData = json.dumps(data, default=self.__serialize_datetime)

            self.logger.info(f'Publishing energyOutput: {jsonData}')

            self.__set_last_energy_output(data)

            self.inverterMqtt.publish_message('energyOutput', jsonData)
        except Exception as e:
            self.logger.error(f'Error in inverter remote panel loop: {e}')

    def __serialize_datetime(obj): 
        if isinstance(obj, datetime.datetime): 
            return obj.isoformat() 
        raise TypeError("Type not serializable") 

    def __set_last_energy_output(self, data):
        with self._last_energy_output_lock:
            self._last_energy_output = dict(data)

    def get_last_energy_output(self):
        with self._last_energy_output_lock:
            if self._last_energy_output is None:
                return None
            return dict(self._last_energy_output)

    def __loop(self):          
        initalRun = False
        
        while self.serviceRunning:

            if initalRun is False and self.inverterMqtt.isConected() is True:
                self.__updateEnergyOutput()
                initalRun = True

            time.sleep(1)


    def start(self):
        self.logger.info('Starting remote panel ...')
        self.inverterMqtt.connect()

        self.serviceRunning = True
        schedule.every().hour.at(":35").do(self.__updateEnergyOutput)

        self.__loop()

        self.inverterMqtt.disconnect()
        
        self.logger.info('Remote panel stopped')

    def stop(self):
        self.logger.info('Stopping remote panel ...')
        self.serviceRunning = False
