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

###Added the post
class PostForm(FlaskForm):
    title = StringField('Title', validators = [DataRequired()] )
    content = TextAreaField('Content',  validators = [DataRequired()] )
    submit = SubmitField('Post')
    

