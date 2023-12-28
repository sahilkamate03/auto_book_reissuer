from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email address', validators=[DataRequired(), Email()])
    user_id = IntegerField('User Id', validators=[DataRequired(), NumberRange(min=1)])
    password = PasswordField('Password', validators=[DataRequired()])
    send_notifications = BooleanField('Send Email Notifications')
    submit = SubmitField('Register / Update')