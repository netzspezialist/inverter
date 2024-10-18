from os.path import abspath, dirname
import sqlite3
import time
from inverter_energy_data import InverterEnergyData
from inverter_mqtt import InverterMqtt

class InverterRemotePanel:
    def __init__(self, logger):
        self.logger = logger
        self.inverterMqtt : InverterMqtt = InverterMqtt(logger)
    
    def __getEnergy(self, direction: str, timestamp: int):
        self.logger.debug(f'Getting energy data [{direction}] from [{timestamp}]')
        self.sql.execute(f'SELECT * FROM Energy{direction} WHERE timestamp = {timestamp}')
        energy = self.sql.fetchone()
        return energy

    def __loop(self):
        while self.serviceRunning:
            try:
                self.logger.debug('Inverter remote panel loop running ...')
                energy = self.__getEnergy('Output', 20240000)
                self.inverterMqtt.publish_message('energyOutput', energy)
                time.sleep(60)
            except Exception as e:
                self.logger.error(f'Error in inverter remote panel loop: {e}')

    def start(self):
        self.logger.info('Starting remote panel ...')

        script_path = abspath(dirname(__file__))
        dbPath = f'{script_path}/inverter.db'
        self.connection = sqlite3.connect(dbPath)
        self.sql = self.connection.cursor()

        

        self.serviceRunning = True
        self.__loop()

        self.connection.close()
        self.inverterMqtt.disconnect()
        
        self.logger.info('Remote panel stopped')

    def stop(self):
        self.logger.info('Stopping remote panel ...')
        self.serviceRunning = False
