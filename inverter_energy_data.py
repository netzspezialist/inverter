import sqlite3
import asyncio

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
            self.sql.execute('INSERT INTO EnergyOutput (timestamp, value) VALUES (0, 0)')
            self.connection.commit()
            totalChanges = self.connection.total_changes
            self.logger.debug(f'Total changes: {totalChanges}')

        #qet = self.inverterCommands.energy()
        #self.sql.execute(f'INSERT INTO energy (timestamp, EnergyOutput) VALUES ("9999", {qet})')

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

        self.logger.info('Inverter monitoring stopped')

    def stop(self):
        self.logger.info('Stopping inverter monitoring ...')
        self.serviceRunning = False               
    
    def getEnergyOutput(self, timestamp: int):
        self.logger.debug(f'Getting energy data from [{timestamp}]')
        self.sql.execute('SELECT * FROM EnergyOutput')
