
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib


class EmailNotification:
    def __init__(self, logger):
        self.logger = logger
        
    def send_email_notification(self, execution_time):
        sender_email = "inverter@netzspezialist.de"
        receiver_email = "hildinger@netzspezialist.de"
        password = os.getenv("EMAIL_PASSWORD")  # Assuming you've set your email password in an environment variable

        message = MIMEMultipart("alternative")
        message["Subject"] = "Inverter Settings Update Notification"
        message["From"] = sender_email
        message["To"] = receiver_email

        text = """\
        Hi,
        The inverter settings were successfully updated at {}.""".format(execution_time.strftime("%Y-%m-%d %H:%M:%S"))
        part = MIMEText(text, "plain")
        message.attach(part)

        try:
            server = smtplib.SMTP_SSL('smtp.example.com', 465)  # Use your SMTP server details
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()
            self.logger.info("Email notification sent successfully.")
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")