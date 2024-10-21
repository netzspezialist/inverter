import datetime
import json
from os.path import abspath, dirname
import sqlite3
import time
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

        self.logger.debug(f'Getting total [Energy{direction}] for years: [{years}]')            
            
        self.sql.execute(f'select sum(value) from Energy{direction} where timestamp in ( {years} )')
        energy = self.sql.fetchone()
        return energy

    def __loop(self):
        while self.serviceRunning:
            try:
                self.logger.debug('Inverter remote panel loop running ...')
                energy = self.__getEnergyToatal('Output')
                data =  {
                    "energy": energy
                }
                jsonData = json.dumps(data)
                self.inverterMqtt.publish_message('energyOutput', jsonData)
                time.sleep(60)
            except Exception as e:
                self.logger.error(f'Error in inverter remote panel loop: {e}')
                time.sleep(60)

    def start(self):
        self.logger.info('Starting remote panel ...')

        script_path = abspath(dirname(__file__))
        dbPath = f'{script_path}/inverter.db'
        self.logger.debug(f'Database path: {dbPath}')
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
