import logging
from logging.handlers import TimedRotatingFileHandler
import os
import signal
import sys
from threading import Thread
from os.path import dirname, abspath
from inverter_connection import InverterConnection
from inverter_monitor import InverterMonitor
from inverter_commands import InverterCommands
from inverter_mqtt import InverterMqtt
from inverter_remotepanel import InverterRemotePanel
from inverter_webapi import InverterWebAPI
from inverter_energy_data import InverterEnergyData

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

script_path = abspath(dirname(__file__))

logPath = f'{script_path}/log'
if not os.path.exists(logPath):
    os.makedirs(logPath)

fileHandler = TimedRotatingFileHandler(f'{logPath}/inverter.log', when='midnight', backupCount=7)
fileHandler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)8s | %(name)s | %(message)s'))
logger.addHandler(fileHandler)

#stdout_handler = logging.StreamHandler()
#stdout_handler.setLevel(logging.DEBUG)
#stdout_handler.setFormatter(logging.Formatter('%(levelname)8s | %(message)s'))
#logger.addHandler(stdout_handler)

class InverterService:
    def __init__(self, logger=None):       
        signal.signal(signal.SIGINT, self.stop) # Ctrl+C
        signal.signal(signal.SIGTERM, self.stop) # Supervisor/process manager signals
        signal.signal(signal.SIGQUIT, self.stop)

        self.logger = logger      

        inverterConnectionLogger = logging.getLogger('connection')
        inverterConnectionLogger.setLevel(logging.INFO)
        inverterConnectionLogger.addHandler(fileHandler)

        self.inverterConnection = InverterConnection(inverterConnectionLogger)
        
        inverterCommandsLogger = logging.getLogger('commands')
        inverterCommandsLogger.setLevel(logging.INFO)
        inverterCommandsLogger.addHandler(fileHandler)
        self.inverterCommands: InverterCommands = InverterCommands(self.inverterConnection, inverterCommandsLogger)

        inverterMonitorLogger = logging.getLogger('monitor')
        inverterMonitorLogger.setLevel(logging.INFO)
        inverterMonitorLogger.addHandler(fileHandler)
        self.inverterMonitor: InverterMonitor = InverterMonitor(inverterMonitorLogger, self.inverterCommands)

        inverterEnergyDataLogger = logging.getLogger('energyData')
        inverterEnergyDataLogger.setLevel(logging.DEBUG)
        inverterEnergyDataLogger.addHandler(fileHandler)
        self.inverterEnergyData: InverterEnergyData = InverterEnergyData(inverterEnergyDataLogger, self.inverterCommands)

        inverterMqttLogger = logging.getLogger('mqtt')
        inverterMqttLogger.setLevel(logging.DEBUG)
        inverterMqttLogger.addHandler(fileHandler)
        self.inverterMqtt : InverterMqtt = InverterMqtt(inverterMqttLogger)
        
        self.inverterRemotePanelLogger = logging.getLogger('remotePanel')
        self.inverterRemotePanelLogger.setLevel(logging.DEBUG)
        self.inverterRemotePanelLogger.addHandler(fileHandler)
        self.inverterRemotePanel = InverterRemotePanel(self.inverterRemotePanelLogger, self.inverterMqtt, self.inverterEnergyData)

        self.inverterWebAPI = InverterWebAPI(logger, self.inverterCommands)
        self.inverterWebAPIThread = Thread(target = self.inverterWebAPI.start)        

    def start(self):
        self.logger.info('Starting inverter service ...')

        self.inverterMonitorThread = Thread(target = self.inverterMonitor.start)
        self.inverterMonitorThread.start()

        self.inverterEnergyDataThread = Thread(target = self.inverterEnergyData.start)
        self.inverterEnergyDataThread.start()
        
        self.inverterMqtt.connect()
        #self.inverterRemotePanel.start()

        
        self.logger.info('Starting inverter web API ...')    
        self.inverterWebAPIThread.start()
        self.logger.info('Inverter web API started ...')    
        self.inverterMonitorThread.join()
        

        self.logger.info('Exit inverter service ...')


    def stop(self):
        self.logger.info('Stopping inverter service ...')
        self.inverterMonitor.stop()
        self.inverterEnergyData.stop()
        self.inverterRemotePanel.stop()

        self.inverterMqtt.disconnect()


if __name__ == '__main__':

    logger.info('Starting inverter service ...')

    inverterService = InverterService(logger)

    try:
        inverterService.start()            
    finally:
        inverterService.stop()
        logger.info('Exit ...')
        os.kill(os.getpid(),signal.SIGKILL)
        logger.info('Exit ...')
        sys.exit(1)        

        