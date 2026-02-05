import logging
import sqlite3
import asyncio
import datetime
import schedule
import time

from os.path import dirname, abspath
from logging import Logger
from inverter_commands import InverterCommands

class InverterEnergyData:
    def __init__(self, logger: Logger, inverterCommands: InverterCommands):        
        self.logger = logger
        self.inverterCommands = inverterCommands
        self.initialRun = True
        
    def __initializeShema(self):
        self.logger.info('Initializing energy data schema...')
        self.sql.execute('CREATE TABLE IF NOT EXISTS EnergyOutput (timestamp INTEGER, value INTEGER)')
        self.sql.execute('CREATE TABLE IF NOT EXISTS EnergyInput (timestamp INTEGER, value INTEGER)')
        self.connection.commit()
        totalChanges = self.connection.total_changes        
        self.logger.debug(f'Total changes: {totalChanges}')
        

    def __writingEnergyData(self):
        self.logger.info('Writing energy data...')
       
        energyFlowCommands =	{
        "Input": "qe",
        "Output": "ql"
        }

        current_year =  datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        current_day = datetime.datetime.now().day

        energyFlows = ["Input", "Output"]

        try:
            for energyFlow in energyFlows:
                year = current_year
                month = current_month
                day = current_day
                
                initDaysCompleted = False
                initMonthsCompleted = False
                initYearsCompleted = False
                
                while not (initDaysCompleted and initMonthsCompleted and initYearsCompleted):
                    timestamp = year * 10000 + month * 100 + day            
                    if day > 0:                        
                        existingValue = self.__getEnergy(energyFlow, timestamp)
                        energy = 0

                        self.logger.debug(f'Updating energy [{energyFlow}] for day [{timestamp}]')
                        
                        if existingValue is None or day == current_day or day == current_day - 1:
                            response = self.inverterCommands.energy(f'{energyFlowCommands[energyFlow]}d', str(timestamp))
                            energy = response["energy"]

                            if existingValue is None:
                                self.__insertEnergy(energyFlow, timestamp, energy)
                            else:
                                if energy > existingValue:
                                    self.__updateEnergy(energyFlow, timestamp, energy)

                        day = day - 1

                    elif month > 0:
                        initDaysCompleted = True

                        existingValue = self.__getEnergy(energyFlow, timestamp)
                        energy = 0

                        self.logger.debug(f'Updating energy [{energyFlow}] for day [{timestamp}]')

                        if existingValue is None or month == current_month or month == current_month -1:
                            response = self.inverterCommands.energy(f'{energyFlowCommands[energyFlow]}m', str(year * 100 + month))
                            energy = response["energy"]

                            if existingValue is None and energy > 0:
                                self.__insertEnergy(energyFlow, timestamp, energy)
                            else:
                                if energy > existingValue:
                                    self.__updateEnergy(energyFlow, timestamp, energy)

                        month = month - 1
                    
                    elif year > 2021:
                        initMonthsCompleted = True
                                    
                        existingValue = self.__getEnergy(energyFlow, timestamp)
                        energy = 0

                        self.logger.debug(f'Updating energy [{energyFlow}] for day [{timestamp}]')

                        if existingValue is None or year == current_year:
                            response = self.inverterCommands.energy(f'{energyFlowCommands[energyFlow]}y', str(year))
                            energy = response["energy"]

                            if existingValue is None:
                                self.__insertEnergy(energyFlow, timestamp, energy)
                            elif year == current_year and energy > existingValue:
                                self.__updateEnergy(energyFlow, timestamp, energy)

                        year = year - 1
                    else:
                        initYearsCompleted = True
                        self.logger.info(f'Updating energy [{energyFlow}] done')

        except Exception as e:
            self.logger.error(f'Writing energy data failed: {e}')
            return

        self.logger.info(f'Updating energy done')
        self.initialRun = True


    def __getEnergy(self, direction: str, timestamp: int):
        self.logger.debug(f'Fetching existing value for Energy{direction} timestamp [{timestamp}]')
        self.sql.execute(f'SELECT value FROM Energy{direction} WHERE timestamp = {timestamp}')
        row = self.sql.fetchone()
        return row[0] if row is not None else None

    def __insertEnergy(self, direction: str, timestamp: int, energy: int):
        self.logger.info(f'Inserting [Energy{direction}] with [{energy}] Wh for [{timestamp}]')
        self.sql.execute(f'INSERT INTO Energy{direction} (timestamp, value) VALUES ({timestamp}, {energy})')
        self.connection.commit()
        totalChanges = self.connection.total_changes
        self.logger.debug(f'Total changes: {totalChanges}')

    def __updateEnergy(self, direction: str, timestamp: int, energy: int):
        self.logger.info(f'Updating [Energy{direction}] to [{energy}] Wh for [{timestamp}]')
        self.sql.execute(f'UPDATE Energy{direction} SET value = {energy} WHERE timestamp = {timestamp}')
        self.connection.commit()
        totalChanges = self.connection.total_changes
        self.logger.debug(f'Total changes: {totalChanges}')

    def __loop(self):          
        while self.serviceRunning:
            schedule.run_pending()
            time.sleep(1)

    def start(self):
        self.logger.info('Starting energy monitoring ...')        
        self.serviceRunning = True

        script_path = abspath(dirname(__file__))
        dbPath = f'{script_path}/inverter.db'
        self.logger.debug(f'Database path: {dbPath}')

        self.connection = sqlite3.connect(dbPath, check_same_thread=False)
        self.sql = self.connection.cursor()
        sqlVersion = self.sql.execute('SELECT SQLITE_VERSION()')
        self.logger.info(f'SQLite version: {sqlVersion.fetchone()}')
        self.__initializeShema()
        
        schedule.every().hour.at(":30").do(self.__writingEnergyData)

        self.__loop()

        self.connection.close()

        self.logger.info('Inverter energy monitoring stopped')

    def stop(self):
        self.logger.info('Stopping energy monitoring ...')
        self.serviceRunning = False               
