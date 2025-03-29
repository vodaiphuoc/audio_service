import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ....setting import SETTINGS

class EmailService:
    @staticmethod
    def send_email(recipient: str, subject: str, body: str):
        msg = MIMEMultipart("alternative")
        msg['From'] = SETTINGS.SMTP_USER
        msg['To'] = recipient
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(SETTINGS.SMTP_HOST, SETTINGS.SMTP_PORT) as server:
            server.starttls()
            server.login(SETTINGS.SMTP_USER, SETTINGS.SMTP_PASSWORD)
            server.send_message(msg)
