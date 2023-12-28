import os
import smtplib
import sqlite3
import time

from cryptography.fernet import Fernet
import mechanicalsoup
import requests
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange

load_dotenv()  
fernet = Fernet(os.getenv("FERNET_KEY"))

app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
DATABASE = "./db/site.db"
class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email address', validators=[DataRequired(), Email()])
    user_id = IntegerField('User Id', validators=[DataRequired(), NumberRange(min=1)])
    password = PasswordField('Password', validators=[DataRequired()])
    send_notifications = BooleanField('Send Email Notifications')
    submit = SubmitField('Register / Update')

def create_table():
    connection = sqlite3.connect(DATABASE)
    with open('./db/schema.sql') as f:
        connection.executescript(f.read())

def add_to_database(name, email, user_id, password, send_notifications, user_ip):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    already_exists = False
    isDataUpdated = True
    try:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            old_mail =existing_user[2]
            cursor.execute("""
                UPDATE users SET name=?, email=?, password=?, send_notifications=?
                WHERE id=?
            """, (name, email, password, send_notifications, existing_user[0]))
            already_exists = True

        else:
            cursor.execute("INSERT INTO users (name, email, user_id, password, send_notifications) VALUES (?, ?, ?, ?, ?)", (name, email, user_id, password, send_notifications))

        connection.commit()
        print("User added/updated successfully")

    except sqlite3.Error as e:
        isDataUpdated = False
        connection.rollback()
    finally:
        connection.close()
        print(isDataUpdated, " ", already_exists) 
        if (isDataUpdated and already_exists == False):
            msg_subject = "New User Registered"
            msg_body =  f"""
            Hi {name},

            Your details have been successfully registered! Here's a summary:

            - Name: {name}
            - Email: {email}
            - User ID: {user_id}
            - Send Notifications: {send_notifications}

            To update your details in the future, please fill out the registration form again.

            If you have any questions or concerns, feel free to contact us.

            Regards,
            Library Reissue Bot
            """
            send_mail(email, msg_subject, msg_body)

        elif (isDataUpdated and already_exists == True and old_mail != email):
            msg_subject = "User Details Updated"
            msg_body =  f"""
            Hi {name},

            Your details have been successfully updated! Here's a summary:

            - Name: {name}
            - Email: {email}
            - User ID: {user_id}
            - Send Notifications: {send_notifications}

            If you have any questions or concerns, feel free to contact us.

            Regards,
            Library Reissue Bot
            """
            # send_mail(email, msg_subject, msg_body)

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


def get_geolocation(ip_address):
    url = 'https://freegeoip.app/json/' + ip_address
    response = requests.get(url)
    data = response.json()
    if data:
        return data['country_name'], data['region_name'], data['city']
    else:
        return None, None, None

def verify_data(user_id, password):
    browser = mechanicalsoup.StatefulBrowser()
    url = "http://14.139.108.229/W27/login.aspx"
    browser.open(url)
    browser.get_current_page()
    browser.select_form()
    browser["txtUserName"] = user_id
    browser["Password1"] = password
    browser.submit_selected()
    span_id = "ctl00_lblUsername"  
    page = browser.page
    messages =page.find_all('span', attrs={"id" : span_id})
    if messages:
        return True
    else:
        return False

@app.route('/register', methods=['GET','POST'])
@limiter.limit("500 per day")
def register():
    
    time.sleep(5)
    user_ip = request.remote_addr
    form = RegistrationForm()
    return redirect(url_for('home', form=form))
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        user_id = form.user_id.data
        password = form.password.data
        encrypted_password = fernet.encrypt(password.encode())
        send_notifications = form.send_notifications.data
        # isDataValid =verify_date(user_id, password)
        # if (isDataValid == False):
        #     flash('Invalid User Id or Password.', 'danger')
        #     return redirect(url_for('register', form=form))
        # print(f"Received data: {name}, {email}, {user_id}, {password}, {send_notifications}")
        add_to_database(name, email, user_id, encrypted_password, send_notifications, user_ip)
        flash('Credentials Saved. Book will be reissued automatically.', 'success')
    return redirect(url_for('home', form=form))

@app.route('/')
def home():
    form = RegistrationForm()
    return render_template('index.html', form=form)

@app.route('/view')
@limiter.limit("100 per minute")
def view():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    connection.close()
    return render_template('view.html', users=users)

if __name__ == "__main__":
    create_table()
    app.run(debug=True)