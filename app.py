import os

from models import RegistrationForm
from services.database import add_to_database, create_table, get_all_users

from cryptography.fernet import Fernet
import mechanicalsoup
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()  
fernet = Fernet(os.getenv("FERNET_KEY"))

app = Flask(__name__)
csrf = CSRFProtect(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[os.getenv('DEFAULT_PER_DAY_LIMIT'), os.getenv('DEFAULT_PER_HOUR_LIMIT')]
)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
create_table()

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
        isDataValid =verify_data(user_id, password)
        if (isDataValid == False):
            flash('Invalid User Id or Password.', 'danger')
            return redirect(url_for('register', form=form))
        add_to_database(name, email, user_id, encrypted_password, send_notifications, user_ip)
        flash('Credentials Saved. Book will be reissued automatically.', 'success')
    return redirect(url_for('home', form=form))

@app.route('/')
def home():
    form = RegistrationForm()
    return render_template('index.html', form=form)

@app.route('/view')
@limiter.limit(os.getenv("FORM_SUBMIT_RATE_LIMIT"))
def view():
    users_data = get_all_users()
    return render_template('view.html', users=users_data)
