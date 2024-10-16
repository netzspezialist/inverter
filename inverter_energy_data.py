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
        self.initialRun = True
        
    def __initializeShema(self):
        self.logger.debug('Initializing schema...')
        self.sql.execute('CREATE TABLE IF NOT EXISTS EnergyOutput (timestamp INTEGER, value INTEGER)')
        self.sql.execute('CREATE TABLE IF NOT EXISTS EnergyInput (timestamp INTEGER, value INTEGER)')
        self.connection.commit()
        totalChanges = self.connection.total_changes        
        self.logger.debug(f'Total changes: {totalChanges}')
        

    async def __writingEnergyData(self):
        self.logger.debug('Initializing energy data...')
       
        current_year = year = datetime.datetime.now().year
        current_month = month = datetime.datetime.now().month
        current_day = day = datetime.datetime.now().day

        initDaysCompleted = False
        initMonthsCompleted = False
        initYearsCompleted = False

        while not (initDaysCompleted and initMonthsCompleted and initYearsCompleted):
            timestamp = year * 10000 + month * 100 + day            
            if day > 0:
                self.logger.debug(f'Updating energy data for day [{timestamp}]')
                loadExists = self.__loadExists(timestamp)
                load = 0
                
                if loadExists is False or day == current_day or day == current_day - 1:
                    response = self.inverterCommands.energy('qld', str(timestamp))
                    load = response["energy"]
                    
                if loadExists is False:
                    self.__insertLoad(timestamp, load)
                elif day == current_day or day == current_day - 1:
                    self.__updateLoad(timestamp, load)
                
                day = day - 1

            elif month > 0:
                initDaysCompleted = True
                if current_month > 0:
                    self.logger.debug(f'Updating energy data for month [{timestamp}]')
                    loadExists = self.__loadExists(timestamp)
                    load = 0

                    if loadExists is False or month == current_month or month == current_month - 1:
                        response = self.inverterCommands.energy('qlm', str(year * 100 + month))
                        load = response["energy"]

                    if loadExists is False:
                        self.__insertLoad(timestamp, load)
                    elif month == current_month:
                        self.__updateLoad(timestamp, load)

                    current_month = current_month - 1
                else:
                    initMonthsCompleted = True
                    if current_year > 2021:
                        self.logger.debug(f'Updating energy data for year [{timestamp}]')
                        loadExists = self.__loadExists(timestamp)
                        load = 0

                        if loadExists is False or year == current_year:
                            response = self.inverterCommands.energy('qly', str(year))
                            load = response["energy"]

                        if loadExists is False:
                            self.__insertLoad(timestamp, load)
                        elif year == current_year:
                            self.__updateLoad(timestamp, load)

                        current_year = current_year - 1
                    else:
                        initYearsCompleted = True

            await asyncio.sleep(5)

        self.initialRun = True

    def __loadExists(self, timestamp: int):
        self.logger.debug(f'Checking if row exists for timestamp [{timestamp}]')
        self.sql.execute(f'select * from EnergyOutput where timestamp = {timestamp}')
        energyOutput = self.sql.fetchone()
        return energyOutput is not None

    def __insertLoad(self, timestamp: int, load: int):
        self.logger.info(f'Inserting load output [{load}] for [{timestamp}]')
        self.sql.execute(f'INSERT INTO EnergyOutput (timestamp, value) VALUES ({timestamp}, {load})')
        self.connection.commit()
        totalChanges = self.connection.total_changes
        self.logger.debug(f'Total changes: {totalChanges}')

    def __updateLoad(self, timestamp: int, load: int):
        self.logger.info(f'Updating load output [{load}] for [{timestamp}]')
        self.sql.execute(f'UPDATE EnergyOutput SET value = {load} WHERE timestamp = {timestamp}')
        self.connection.commit()
        totalChanges = self.connection.total_changes
        self.logger.debug(f'Total changes: {totalChanges}')

    async def __loop(self):

        script_path = abspath(dirname(__file__))
        dbPath = f'{script_path}/inverter.db'
        self.logger.debug(f'Database path: {dbPath}')

        self.connection = sqlite3.connect(dbPath)
        self.sql = self.connection.cursor()
        sqlVersion = self.sql.execute('SELECT SQLITE_VERSION()')
        self.logger.info(f'SQLite version: {sqlVersion.fetchone()}')
        self.__initializeShema()        

        while self.serviceRunning:
            try:
                self.logger.debug('Inverter energy data loop running ...')
                self.__writingEnergyData()
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
