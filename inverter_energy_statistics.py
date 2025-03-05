import datetime
import json
from os.path import abspath, dirname
import sqlite3
import time


class InverterEnergyStatistics:
    def __init__(self, logger):
        self.logger = logger
        self.conn = self.create_connection()
        script_path = abspath(dirname(__file__))
        dbPath = f'{script_path}/inverter.db'
        self.logger.debug(f'Database path: {dbPath}')
        self.connection = sqlite3.connect(dbPath, check_same_thread=False)
        self.sql = self.connection.cursor()
    
    def close(self):
        self.connection.close()
    
    def getEnergyToatal(self, direction: str):        
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
    
    def getEnergyDay(self, direction: str, yesterday: bool):
        timestamp = datetime.datetime.now()
        if yesterday:
            timestamp = timestamp - datetime.timedelta(days=1)
        timestamp = timestamp.strftime('%Y%m%d')
        self.logger.debug(f'Getting total [Energy{direction}] for [{timestamp}]')
        self.sql.execute(f'select value from Energy{direction} where timestamp = {timestamp}')
        energy = self.sql.fetchone()
        return energy[0] if energy is not None else 0

    def getEnergyLastDays(self, direction: str, days: int):
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
    
    
    def getEnergyLast12Months(self, direction: str):

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