import sqlite3

from inverter_commands import InverterCommands

class InverterEnergyData:
    def __init__(self, logger, inverterCommands):        
        self.logger = logger
        self.inverterCommands = inverterCommands
        self.connection = sqlite3.connect('inverter.db')
        totalChanges = self.connection.total_changes
        self.logger.debug(f'Total changes: {totalChanges}')
        self.sql = self.connection.cursor()

        sqlVersion = self.sql.execute('SELECT SQLITE_VERSION()')
        self.logger.debug(f'SQLite version: {sqlVersion.fetchone()}')
        
    def initializeShema(self):
        self.logger.debug('Initializing schema...')
        self.sql.execute('CREATE TABLE IF NOT EXISTS EnergyOutput (timestamp TEXT, input INTEGER, output INTEGER)')
        self.connection.commit()

    def InitializeData(self):
        self.logger.debug('Initializing energy data...')
        qet = self.inverterCommands.energy()
        self.sql.execute(f'INSERT INTO energy (timestamp, EnergyOutput) VALUES ("9999", {qet})')
    
    def getEnergyOutput(self, timestamp):
        self.logger.debug(f'Getting energy data from [{timestamp}]')
        self.sql.execute('SELECT * FROM EnergyOutput')
