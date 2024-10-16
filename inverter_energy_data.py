import sqlite3
import asyncio
import datetime

from os.path import dirname, abspath
from logging import Logger
from inverter_commands import InverterCommands

class InverterEnergyData:
    def __init__(self, logger: Logger, inverterCommands: InverterCommands):        
        self.logger = logger
        self.inverterCommands = inverterCommands

        script_path = abspath(dirname(__file__))
        dbPath = f'{script_path}/inverter.db'
        self.logger.debug(f'Database path: {dbPath}')

        self.connection = sqlite3.connect(dbPath)
        self.sql = self.connection.cursor()
        sqlVersion = self.sql.execute('SELECT SQLITE_VERSION()')
        self.logger.info(f'SQLite version: {sqlVersion.fetchone()}')
        self.__initializeShema()
        self.__initializeData()
        
    def __initializeShema(self):
        self.logger.debug('Initializing schema...')
        self.sql.execute('CREATE TABLE IF NOT EXISTS EnergyOutput (timestamp INTEGER, value INTEGER)')
        self.sql.execute('CREATE TABLE IF NOT EXISTS EnergyInput (timestamp INTEGER, value INTEGER)')
        self.connection.commit()
        totalChanges = self.connection.total_changes        
        self.logger.debug(f'Total changes: {totalChanges}')
        

    def __initializeData(self):
        self.logger.debug('Initializing energy data...')
        res = self.sql.execute('SELECT * FROM EnergyOutput')
        if res.fetchone() is None:
            self.logger.debug('No energy data found. Initializing data ...')          
            current_year = datetime.datetime.now().year
            current_month = datetime.datetime.now().month
            current_day = datetime.datetime.now().day
            initDaysCompleted = False
            initMonthsCompleted = False
            initYearsCompleted = False

            while not (initDaysCompleted and initMonthsCompleted and initYearsCompleted):
                timestamp = current_year * 10000 + current_month * 100 + current_day
                self.logger.debug(f'Initializing energy data for day [{timestamp}]')
                if current_day > 0:
                    current_day = current_day - 1
                else:
                    initDaysCompleted = True
                    if current_month > 0:
                        current_month = current_month - 1
                    else:
                        initMonthsCompleted = True
                        if current_year > 2021:
                            current_year = current_year - 1
                        else:
                            initYearsCompleted = True
                    
                #self.sql.execute(f'INSERT INTO EnergyOutput (timestamp, value) VALUES ({i}, {i})')
                #self.connection.commit()
                #totalChanges = self.connection.total_changes
                #self.logger.debug(f'Total changes: {totalChanges}')


    async def __loop(self):
        self.logger.info('Inverter energy data loop started')
        while self.serviceRunning:
            try:
                self.logger.debug('Inverter energy data loop running ...')
                
                await asyncio.sleep(60)
            except Exception as e:
                self.logger.error(f'Error in inverter energy data loop: {e}')
            finally:
                pass


    def start(self):
        self.logger.info('Starting energy monitoring ...')        
        self.serviceRunning = True

        loop = asyncio.new_event_loop()
        loop.create_task(self.__loop())
        try:
            loop.run_forever()      
        finally:
            loop.close()

        self.logger.info('Inverter energy monitoring stopped')

    def stop(self):
        self.logger.info('Stopping energy monitoring ...')
        self.serviceRunning = False               
    
    def getEnergyOutput(self, timestamp: int):
        self.logger.debug(f'Getting energy data from [{timestamp}]')
        self.sql.execute('SELECT * FROM EnergyOutput')
