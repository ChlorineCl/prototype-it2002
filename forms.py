from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    username = StringField('Username', validators = [DataRequired(), Length(max = 32)])
    password = PasswordField('Password', validators = [DataRequired(), Length(max = 32)])
    confirm_password = PasswordField('Confirm Password', validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired(), Length(max = 32)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class PostForm(FlaskForm):
    isbn10 = StringField('ISBN-10', validators=[DataRequired()])
    availability = BooleanField('Availability', default=True)
    submit = SubmitField('Create Post')

class UpdateForm(FlaskForm):
    isbn10 = StringField('ISBN-10', validators=[DataRequired()])
    availability = BooleanField('Availability')
    submit = SubmitField('Update post availability')