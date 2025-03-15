
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
from inverter_energy_statistics import InverterEnergyStatistics
import schedule
import datetime
import time

from inverter_config import emailNotification as config

class EmailNotification:
    def __init__(self, logger, inverterEnergyStatistics: InverterEnergyStatistics):
        self.logger = logger
        self.inverterEnergyStatistics = inverterEnergyStatistics
        
    def __send_email_notification(self):

        self.logger.info('Email notification ...')

        sender_email = config["sender_email"]
        receiver_email = config["receiver_email"]
        smtpServer = config["smtp_server"]
        smtpUsername = config["smtp_username"]
        smtpPassword = config["smtp_password"]

        # Check if any of the environment variables are empty
        if not sender_email or not receiver_email or not smtpServer or not smtpUsername or not smtpPassword:
            self.logger.error("One or more environment variables are not set.")
            return

        protocolDate = datetime.datetime.now().strftime("%Y-%m-%d")
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Wechselrichterprotokoll {protocolDate}"
        message["From"] = sender_email
        message["To"] = receiver_email

        energyTotal = round(self.inverterEnergyStatistics.getEnergyToatal('Output') / 1000, 2)
        energyLast12Months = round(self.inverterEnergyStatistics.getEnergyLast12Months('Output') / 1000, 2)
        energyLast30Days = round(self.inverterEnergyStatistics.getEnergyLastDays('Output', 30) / 1000, 2)
        energyLast7Days = round(self.inverterEnergyStatistics.getEnergyLastDays('Output', 7) / 1000, 2)
        energyYesterday = round(self.inverterEnergyStatistics.getEnergyDay('Output', True) / 1000, 2)

        text = f"""
        ### Wechselrichterprotokoll vom {protocolDate} ###

        Gesamtenergie: {energyTotal} kWh
        Energie letzte 12 Monate: {energyLast12Months} kWh
        Energie letzte 30 Tage: {energyLast30Days} kWh
        Energie letzte 7 Tage: {energyLast7Days} kWh
        Energie gestern: {energyYesterday} kWh
        """

        self.logger.info(text)

        part = MIMEText(text, "plain")
        message.attach(part)

        try:
            server = smtplib.SMTP(smtpServer)  # Use your SMTP server details
            server.connect(smtpServer, 587)
            server.ehlo()
            server.starttls()
            server.login(smtpUsername, smtpPassword)
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()
            self.logger.info("Email notification sent successfully.")
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")

    def __loop(self):          
        initalRun = False
        
        while self.serviceRunning:
            schedule.run_pending()
            time.sleep(60)

            if initalRun is False:
                self.__send_email_notification()
                initalRun = True

    def start(self):
        self.logger.info('Starting email notification service ...')

        if not config["enabled"]:
            self.logger.info('Email notification service is disabled')
            return

        self.serviceRunning = True
        schedule.every().day.at("00:10").do(self.__send_email_notification)

        self.__loop()
        
        self.logger.info('Email notification stopped')

    def stop(self):
        self.logger.info('Stopping email notification ...')
        self.serviceRunning = False            