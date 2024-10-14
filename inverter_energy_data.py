import sqlite3

from logging import Logger
from inverter_commands import InverterCommands

class InverterEnergyData:
    def __init__(self, logger: Logger, inverterCommands: InverterCommands):        
        self.logger = logger
        self.inverterCommands = inverterCommands
        self.connection = sqlite3.connect('inverter.db')
        totalChanges = self.connection.total_changes
        self.logger.debug(f'Total changes: {totalChanges}')
        self.sql = self.connection.cursor()
        sqlVersion = self.sql.execute('SELECT SQLITE_VERSION()')
        self.logger.info(f'SQLite version: {sqlVersion.fetchone()}')
        self.__initializeShema()
        
    def __initializeShema(self):
        self.logger.debug('Initializing schema...')
        self.sql.execute('CREATE TABLE IF NOT EXISTS EnergyOutput (timestamp INTEGER, value INTEGER)')
        self.sql.execute('CREATE TABLE IF NOT EXISTS EnergyInput (timestamp INTEGER, value INTEGER)')
        self.connection.commit()
        totalChanges = self.connection.total_changes        
        self.logger.debug(f'Total changes: {totalChanges}')
        self.__initializeData()

    def __initializeData(self):
        self.logger.debug('Initializing energy data...')
        #qet = self.inverterCommands.energy()
        #self.sql.execute(f'INSERT INTO energy (timestamp, EnergyOutput) VALUES ("9999", {qet})')
    
    def getEnergyOutput(self, timestamp: int):
        self.logger.debug(f'Getting energy data from [{timestamp}]')
        self.sql.execute('SELECT * FROM EnergyOutput')
