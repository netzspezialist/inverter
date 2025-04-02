import logging
from logging.handlers import TimedRotatingFileHandler
import os
import signal
import sys
from threading import Thread
from os.path import dirname, abspath
import threading
from inverter_connection import InverterConnection
from inverter_email_notification import EmailNotification
from inverter_energy_statistics import InverterEnergyStatistics
from inverter_monitor import InverterMonitor
from inverter_commands import InverterCommands
from inverter_mqtt import InverterMqtt
from inverter_remotepanel import InverterRemotePanel
from inverter_webapi import InverterWebAPI
from inverter_energy_data import InverterEnergyData
from smartbms import SmartBatteryManagementSystem

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
        inverterEnergyDataLogger.setLevel(logging.INFO)
        inverterEnergyDataLogger.addHandler(fileHandler)
        self.inverterEnergyData: InverterEnergyData = InverterEnergyData(inverterEnergyDataLogger, self.inverterCommands)

        self.energyStatisticsLogger = logging.getLogger('energyStatistics')
        self.energyStatisticsLogger.setLevel(logging.INFO)
        self.energyStatisticsLogger.addHandler(fileHandler)
        self.energyStatistics = InverterEnergyStatistics(self.energyStatisticsLogger)
       
        self.inverterRemotePanelLogger = logging.getLogger('remotePanel')
        self.inverterRemotePanelLogger.setLevel(logging.INFO)
        self.inverterRemotePanelLogger.addHandler(fileHandler)
        self.inverterRemotePanel = InverterRemotePanel(self.inverterRemotePanelLogger, self.energyStatistics)

        self.inverterEmailNotificationLogger = logging.getLogger('emailNotification')
        self.inverterEmailNotificationLogger.setLevel(logging.INFO)
        self.inverterEmailNotificationLogger.addHandler(fileHandler)
        self.inverterEmailNotification = EmailNotification(self.inverterEmailNotificationLogger, self.energyStatistics)

        self.smartbmsLogger = logging.getLogger('smartbms')
        self.smartbmsLogger.setLevel(logging.INFO)
        self.smartbmsLogger.addHandler(fileHandler)
        self.smartbms = SmartBatteryManagementSystem(self.smartbmsLogger, self.inverterCommands)      

        self.inverterWebAPI = InverterWebAPI(logger, self.inverterCommands)
        self.inverterWebAPIThread = Thread(target = self.inverterWebAPI.start)        

    def start(self):
        self.logger.info('Starting inverter service ...')

        self.inverterMonitorThread = Thread(name='Monitor', target = self.inverterMonitor.start)
        self.inverterMonitorThread.start()

        self.inverterEnergyDataThread = Thread(name='EnergyData', target = self.inverterEnergyData.start)
        self.inverterEnergyDataThread.start()
        
        self.inverterRemotePanelThread = Thread(name='RemotePanel', target = self.inverterRemotePanel.start)
        self.inverterRemotePanelThread.start()

        self.inverterEmailNotificationThread = Thread(name='EmailNotification', target = self.inverterEmailNotification.start)
        self.inverterEmailNotificationThread.start()

        self.smartbmsThread = Thread(name='SmartBMS', target = self.smartbms.start)
        self.smartbmsThread.start()

        for thread in threading.enumerate(): 
            self.logger.info(f'Thread: {[thread.name]}')
        
        self.logger.info('Starting inverter web API ...')    
        self.inverterWebAPIThread.start()
        self.logger.info('Inverter web API started ...')    

        self.inverterMonitorThread.join()
        self.inverterEnergyDataThread.join()
        self.inverterRemotePanelThread.join()
        self.inverterEmailNotificationThread.join()
        self.smartbmsThread.join()
            
        self.logger.info('Exit inverter service ...')


    def stop(self):
        self.logger.info('Stopping inverter service ...')
        self.inverterMonitor.stop()
        self.inverterEnergyData.stop()
        self.inverterRemotePanel.stop()
        self.inverterEmailNotification.stop()
        self.energyStatistics.close()

        #self.inverterMqtt.disconnect()


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

        