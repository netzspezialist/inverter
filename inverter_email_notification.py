
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
from inverter_energy_statistics import InverterEnergyStatistics
import schedule
import datetime
import time


class EmailNotification:
    def __init__(self, logger, inverterEnergyStatistics: InverterEnergyStatistics):
        self.logger = logger
        self.inverterEnergyStatistics = inverterEnergyStatistics
        
    def __send_email_notification(self):

        self.logger.info('Email notification ...')

        sender_email = os.getenv("INVERTER_SENDER_EMAIL")  # Assuming you've set your email in an environment variable
        receiver_email = os.getenv("INVERTER_RECEIVER_EMAIL")  # Assuming you've set the receiver email in an environment variable
        smtpServer = os.getenv("INVERTER_SMTP_SERVER")  # Assuming you've set your SMTP server in an environment variable
        smtpUsername = os.getenv("INVERTER_SMTP_USERNAME")  # Assuming you've set your email username in an environment variable
        smtpPassword = os.getenv("INVERTER_SMTP_PASSWORD")  # Assuming you've set your email password in an environment variable

        message = MIMEMultipart("alternative")
        message["Subject"] = "Inverter energy output notification"
        message["From"] = sender_email
        message["To"] = receiver_email

        energyTotal = round(self.inverterEnergyStatistics.getEnergyToatal('Output') / 1000, 2)
        energyLast12Months = round(self.inverterEnergyStatistics.getEnergyLast12Months('Output') / 1000, 2)
        energyLast30Days = round(self.inverterEnergyStatistics.getEnergyLastDays('Output', 30) / 1000, 2)
        energyLast7Days = round(self.inverterEnergyStatistics.getEnergyLastDays('Output', 7) / 1000, 2)
        energyYesterday = round(self.inverterEnergyStatistics.getEnergyDay('Output', True) / 1000, 2)

        text = f"""
        ### Inverter statistics notification ###

        Gesamtenergie: {energyTotal}
        Energie letzte 12 Monate: {energyLast12Months}
        Energie letzte 30 Tage: {energyLast30Days}
        Energie letzte 7 Tage: {energyLast7Days}
        Energie gestern: {energyYesterday}
        
        {datetime.datetime.now().strftime("%Y-%m-%d")}
        """

        self.logger.info(text)

        part = MIMEText(text, "plain")
        message.attach(part)

        try:
            server = smtplib.SMTP_SSL()  # Use your SMTP server details
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
            time.sleep(10)

            if initalRun is False:
                self.__send_email_notification()
                initalRun = True

    def start(self):
        self.logger.info('Starting email notification service ...')

        self.serviceRunning = True
        schedule.every().day.at("00:10").do(self.__send_email_notification)

        self.__loop()
        
        self.logger.info('Email notification stopped')

    def stop(self):
        self.logger.info('Stopping email notification ...')
        self.serviceRunning = False            