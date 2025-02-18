from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
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

class BorrowForm(FlaskForm):
    post_id = IntegerField('Post ID', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    isbn10 = StringField('ISBN-10', validators=[DataRequired()])
    owner = StringField('Owner', validators=[DataRequired()])
    submit = SubmitField('Borrow')

class ReturnForm(FlaskForm):
    post_id = IntegerField('Post ID', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    isbn10 = StringField('ISBN-10', validators=[DataRequired()])
    owner = StringField('Owner', validators=[DataRequired()])
    submit = SubmitField('Return')

class AddBookForm(FlaskForm):
    isbn10 = StringField('ISBN-10', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    publisher = StringField('Publisher', validators=[DataRequired()])
    genre = StringField('Genres', validators=[DataRequired()])
    submit = SubmitField('Add')

class ISBN10Form(FlaskForm):
    isbn10 = StringField('ISBN-10', validators=[DataRequired()])
    submit = SubmitField('Update this book')

class UpdateBookForm(FlaskForm):
    isbn10 = StringField('ISBN-10', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    publisher = StringField('Publisher', validators=[DataRequired()])
    genre = StringField('Genres', validators=[DataRequired()])
    submit = SubmitField('Update')

class DeleteBookForm(FlaskForm):
    isbn10 = StringField('ISBN-10', validators=[DataRequired()])
    submit = SubmitField('Delete')

class DeleteUserForm(FlaskForm):
    email = StringField('User Email', validators=[DataRequired()])
    submit = SubmitField('Delete')
    
FILTER_DATE = [
    ('Most Recent', 'Most Recent'),
    ('Oldest', 'Oldest')
]

FILTER_ALPHABET = [
    ('A -> Z', 'A -> Z'),
    ('Z -> A', 'Z -> A')
]

FILTER_GENRE = []