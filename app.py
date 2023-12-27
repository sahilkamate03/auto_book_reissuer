import mechanicalsoup
import sqlite3

from flask import Flask, render_template,redirect, url_for, flash

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange

app = Flask(__name__)
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

def add_to_database(name, email, user_id, password, send_notifications):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO users (name, email, user_id, password, send_notifications) VALUES (?, ?, ?, ?, ?)", (name, email, user_id, password, send_notifications))
    connection.commit()
    connection.close()

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
    print(messages)
    if messages:
        return True
    else:
        return False

@app.route('/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    print ('hello')
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
        print(f"Received data: {name}, {email}, {user_id}, {password}, {send_notifications}")
        add_to_database(name, email, user_id, password, send_notifications)
        flash('Credentials Saved. Book will be reissued automatically.', 'success')
        return redirect(url_for('register', form=form))

    return render_template('index.html', form=form)

@app.route('/view')
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