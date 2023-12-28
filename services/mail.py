import os
import smtplib
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

def send_mail(email,subject, body):
    sender = os.getenv('EMAIL')
    recipient = email
    subject = subject

    body = body

    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = os.getenv('EMAIL')
    smtp_password = os.getenv('EMAIL_PWD')

    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(smtp_username, smtp_password)
        smtp.sendmail(sender, recipient, message.as_string())
