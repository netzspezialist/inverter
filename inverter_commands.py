import re

from datetime import datetime
from inverter_connection import InverterConnection
from inverter_response import InverterResponseConverter

REGEX_INVERTER_FLOAT = '[0-9][0-9]\.[0-9]'

class InverterCommands:
    def __init__(self, inverterConnection : InverterConnection, logger=None):
        self.inverterConnection = inverterConnection
        self.logger = logger

    def qpigs(self):
        self.logger.debug('Getting qpigs...')
        startTime = datetime.now()        
        response1 = self.inverterConnection.execute("QPIGS")
        self.logger.debug(f'qpigs result: {response1}')
        response2 = self.inverterConnection.execute("QPIGS2")
        self.logger.debug(f'qpigs result: {response2}')
        stopTime = datetime.now()

        command = "qpigs"
        timestamp = InverterResponseConverter.createTimeStamp(startTime, stopTime)

        data = InverterResponseConverter.qpigs(command, timestamp, response1, response2)

        self.logger.debug(f'qpigs data: {data}')

        return data    
    
    def qpiri(self):
        self.logger.debug('Getting QPIRI...')
        startTime = datetime.now()        
        response = self.inverterConnection.execute("QPIRI")
        stopTime = datetime.now()
        self.logger.debug(f'qpiri result: {response}')

        command = "qpiri"
        timestamp = InverterResponseConverter.createTimeStamp(startTime, stopTime)

        data = InverterResponseConverter.qpiri(command, timestamp, response)

        self.logger.debug(f'qpiri data: {data}')

        return data
    
    def energy(self):
        self.logger.debug('Getting energy...')
        startTime = datetime.now()        
        response = self.inverterConnection.execute("QET")
        stopTime = datetime.now()
        self.logger.info(f'energy result: {response}')

        command = "QET"
        timestamp = InverterResponseConverter.createTimeStamp(startTime, stopTime)

        data = InverterResponseConverter.qet(command, timestamp, response)

        self.logger.debug(f'energy data: {data}')

        return data
    
    def updateSetting(self, setting, value):
        self.logger.info(f'Updating inverter setting [{setting}] with value [{value}]')
        
        if setting == "batteryBulkVoltage":
            if not re.search(REGEX_INVERTER_FLOAT, value):
                raise ValueError("Invalid value for batteryBulkVoltage")                                             
            command = f"PCVV{value}"
        
        elif setting == "batteryFloatVoltage":
            if not re.search(REGEX_INVERTER_FLOAT, value):
                raise ValueError("Invalid value for batteryBulkVoltage")
            command = f"PBFT{value}"                      
        else:
            raise ValueError("Invalid setting")

        startTime = datetime.now()     
        response = self.inverterConnection.execute(command)            
        stopTime = datetime.now()

        self.logger.debug(f'response: {response}')


        timestamp = InverterResponseConverter.createTimeStamp(startTime, stopTime)

        updateSettingResult = InverterResponseConverter.updateSetting(command, timestamp, response)

        self.logger.debug(f'update setting result: {updateSettingResult}')

        return updateSettingResult