import datetime
import json
from os.path import abspath, dirname
import sqlite3
import time
from inverter_energy_statistics import InverterEnergyStatistics
import schedule
from inverter_mqtt import InverterMqtt

class InverterRemotePanel:
    def __init__(self, logger, inverterEnergyStatistics: InverterEnergyStatistics):
        self.logger = logger
        self.inverterMqtt : InverterMqtt = InverterMqtt(logger)
        self.inverterEnergyStatistics = inverterEnergyStatistics
    
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

            self.inverterMqtt.publish_message('energyOutput', jsonData)
        except Exception as e:
            self.logger.error(f'Error in inverter remote panel loop: {e}')

    def __serialize_datetime(obj): 
        if isinstance(obj, datetime.datetime): 
            return obj.isoformat() 
        raise TypeError("Type not serializable") 

    def __loop(self):          
        initalRun = False
        
        while self.serviceRunning:
            schedule.run_pending()
            time.sleep(10)

            if initalRun is False and self.inverterMqtt.isConected() is True:
                self.__updateEnergyOutput()
                initalRun = True

    def start(self):
        self.logger.info('Starting remote panel ...')
        self.inverterMqtt.connect()

        self.serviceRunning = True
        schedule.every().hour.at(":05").do(self.__updateEnergyOutput)

        self.__loop()

        self.inverterMqtt.disconnect()
        
        self.logger.info('Remote panel stopped')

    def stop(self):
        self.logger.info('Stopping remote panel ...')
        self.serviceRunning = False
