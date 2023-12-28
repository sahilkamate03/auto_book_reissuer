import os
import sqlite3
import time

from models import RegistrationForm
from services.database import add_to_database, create_table, DATABASE

from cryptography.fernet import Fernet
import mechanicalsoup
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


load_dotenv()  
fernet = Fernet(os.getenv("FERNET_KEY"))

app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")


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
    user_ip = request.remote_addr
    form = RegistrationForm()
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