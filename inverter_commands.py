import re

from datetime import datetime
from inverter_connection import InverterConnection
from inverter_response import InverterResponseConverter

REGEX_INVERTER_FLOAT = '[0-9][0-9]\.[0-9]'
REGEX_INVERTER_INT = '[0-9][0-9][0-9]'

ENERGY_COMMANDS = { 
    "QET": "^$", 
    "QEY": "^[0-9][0-9][0-9][0-9]$", 
    "QEM": "^[0-9][0-9][0-9][0-9][0-1][0-9]$", 
    "QED": "^[0-9][0-9][0-9][0-9][0-1][0-9][0-3][0-9]$", 
    "QLT": "^$", 
    "QLY": "^[0-9][0-9][0-9][0-9]$", 
    "QLM": "^[0-9][0-9][0-9][0-9][0-1][0-9]$", 
    "QLD": "^[0-9][0-9][0-9][0-9][0-1][0-9][0-3][0-9]$", 
}
  


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
    
    def energy(self, command: str, timestamp: int):
        self.logger.debug(f'Getting energy data [{command}{timestamp}]')

        command = command.upper()

        commandValidator = ENERGY_COMMANDS.get(command)

        if commandValidator is None:
            raise ValueError("Invalid command")
        
        if not re.search(commandValidator, timestamp):
            raise ValueError("Invalid command value")
        
        command = f"{command}{timestamp}"

        startTime = datetime.now()        
        response = self.inverterConnection.execute(command)
        stopTime = datetime.now()
        self.logger.info(f'energy command: {command} result: {response}')

        timestamp = InverterResponseConverter.createTimeStamp(startTime, stopTime)

        data = InverterResponseConverter.energy(command, timestamp, response, self.logger)

        self.logger.debug(f'energy data: {data}')

        return data
    
    def updateSetting(self, setting: str, value: str):
        self.logger.info(f'Updating inverter setting [{setting}] with value [{value}]')
        
        if setting == "batteryBulkVoltage":
            if not re.search(REGEX_INVERTER_FLOAT, value):
                raise ValueError("Invalid value for batteryBulkVoltage")                                             
            command = f"PCVV{value}"
        
        elif setting == "batteryFloatVoltage":
            if not re.search(REGEX_INVERTER_FLOAT, value):
                raise ValueError("Invalid value for batteryBulkVoltage")
            command = f"PBFT{value}"                      
        
        elif setting == "batteryMaxChargingCurrent":
            if not re.search(REGEX_INVERTER_INT, value):
                raise ValueError("Invalid value for batteryMaxChargingCurrent")
            command = f"MNCHGC0{value}"

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