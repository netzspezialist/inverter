import datetime
import json
from os.path import abspath, dirname
import sqlite3
import time
import schedule
from inverter_energy_data import InverterEnergyData
from inverter_mqtt import InverterMqtt

class InverterRemotePanel:
    def __init__(self, logger):
        self.logger = logger
        self.inverterMqtt : InverterMqtt = InverterMqtt(logger)
    
    def __getEnergyToatal(self, direction: str):        
        currentYear = datetime.datetime.now().year
        
        years = '20220000'
        year = 2023
        while year <= currentYear:
            timestamp = year * 10000
            years += f', {timestamp}'
            year += 1

        self.logger.debug(f'Getting [Energy{direction}] for years: [{years}]')            
            
        self.sql.execute(f'select sum(value) from Energy{direction} where timestamp in ( {years} )')
        energy = self.sql.fetchone()
        return energy[0] if energy is not None else 0
    
    def __getEnergyDay(self, direction: str, yesterday: bool):
        timestamp = datetime.datetime.now()
        if yesterday:
            timestamp = timestamp - datetime.timedelta(days=1)
        timestamp = timestamp.strftime('%Y%m%d')
        self.logger.debug(f'Getting total [Energy{direction}] for [{timestamp}]')
        self.sql.execute(f'select value from Energy{direction} where timestamp = {timestamp}')
        energy = self.sql.fetchone()
        return energy[0] if energy is not None else 0

    def __getEnergyLastDays(self, direction: str, days: int):
        currentDay = datetime.datetime.now() -datetime.timedelta(days=1)
        timestamp = currentDay.year * 10000 + currentDay.month * 100 + currentDay.day      
        timestamps = f'{timestamp}'

        for i in range(1, days):
            currentDay = currentDay - datetime.timedelta(days=1)
            timestamp = currentDay.year * 10000 + currentDay.month * 100 + currentDay.day
            timestamps += f', {timestamp}'

        self.logger.debug(f'Getting [Energy{direction}] for last [{days}] days: [{timestamps}]')

        self.sql.execute(f'select sum(value) from Energy{direction} where timestamp in ( {timestamps} )')
        energy = self.sql.fetchone()
        return energy[0] if energy is not None else 0        
    
    
    def __getEnergyLast12Months(self, direction: str):

        year = datetime.datetime.now().year
        month = datetime.datetime.now().month - 1

        if month == 0:
            month = 12
            year -= 1
       
        timestamp = year * 10000 + month * 100
        timestamps = f'{timestamp}'

        for i in range(1, 12):
            
            month = month - 1

            if month == 0:
                month = 12
                year -= 1

            timestamp = year * 10000 + month * 100
            timestamps += f', {timestamp}'
        
        self.logger.debug(f'Getting [Energy{direction}] for last 12 months [{timestamps}]')
        self.sql.execute(f'select sum(value) from Energy{direction} where timestamp in ( {timestamps} )')
        energy = self.sql.fetchone()
        return energy[0] if energy is not None else 0

    def __updateEnergyOutput(self):
        try:
            self.logger.debug('Inverter remote panel loop running ...')
            energyTotal = self.__getEnergyToatal('Output')
            energyLast12Months = self.__getEnergyLast12Months('Output')
            energyLast30Days = self.__getEnergyLastDays('Output', 30)
            energyLast7Days = self.__getEnergyLastDays('Output', 7)
            energyYesterday = self.__getEnergyDay('Output', True)
            energyToday = self.__getEnergyDay('Output', False)
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

        script_path = abspath(dirname(__file__))
        dbPath = f'{script_path}/inverter.db'
        self.logger.debug(f'Database path: {dbPath}')
        self.connection = sqlite3.connect(dbPath, check_same_thread=False)
        self.sql = self.connection.cursor()

        self.serviceRunning = True
        schedule.every().hour.at(":01").do(self.__updateEnergyOutput)

        self.__loop()

        self.connection.close()
        self.inverterMqtt.disconnect()
        
        self.logger.info('Remote panel stopped')

    def stop(self):
        self.logger.info('Stopping remote panel ...')
        self.serviceRunning = False
