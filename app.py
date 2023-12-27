import mechanicalsoup
import sqlite3
import os
from dotenv import load_dotenv
import requests

from flask import Flask, render_template,redirect, url_for, flash, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()  

app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
app.config['SECRET_KEY'] = '7253b6bb628eaea304a5dc18c17c4cc003b822835f1963ad'
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

    try:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            old_mail =existing_user[2]
            cursor.execute("""
                UPDATE users SET name=?, email=?, password=?, send_notifications=?
                WHERE id=?
            """, (name, email, password, send_notifications, existing_user[0]))
            # send_mail(old_mail, "Alert: User Details Updated", f"Your user details have been updated. \n\nName: {name}\nEmail: {email}\nUser Id: {user_id}\nPassword: {password}\nSend Notifications: {send_notifications}\nDetails are updated by IP Address {user_ip} at {get_geolocation(user_ip)} \n\nRegards,\nLibrary Reissue Bot")

        else:
            cursor.execute("INSERT INTO users (name, email, user_id, password, send_notifications) VALUES (?, ?, ?, ?, ?)", (name, email, user_id, password, send_notifications))

        connection.commit()

        
        print("User added/updated successfully")

    except sqlite3.Error as e:
        print("Error:", e)
        connection.rollback()
    finally:
        connection.close()

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

def verify_date(user_id, password):
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
    user_ip = request.remote_addr
    form = RegistrationForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        user_id = form.user_id.data
        password = form.password.data
        send_notifications = form.send_notifications.data
        # isDataValid =verify_date(user_id, password)
        # if (isDataValid == False):
        #     flash('Invalid User Id or Password.', 'danger')
        #     return redirect(url_for('register', form=form))
        # print(f"Received data: {name}, {email}, {user_id}, {password}, {send_notifications}")
        add_to_database(name, email, user_id, password, send_notifications, user_ip)
        flash('Credentials Saved. Book will be reissued automatically.', 'success')
    return redirect(url_for('register', form=form))

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