from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,BooleanField,DateField,IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp
from wtforms import SelectField, DateField, SubmitField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=30)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = StringField('Address', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired(), Regexp(r'^\d{10}$', message="Enter a valid 10-digit number")])
    pincode = StringField('Pin Code', validators=[DataRequired(), Regexp(r'^\d{6}$', message="Enter a valid 6-digit pincode")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
class FlightSearchForm(FlaskForm):
    origin = SelectField('From', choices=[
        ('Delhi', 'Delhi'),
        ('Mumbai', 'Mumbai'),
        ('Chennai', 'Chennai'),
        ('Bangalore', 'Bangalore'),
        ('Kolkata', 'Kolkata'),
        ('Hyderabad', 'Hyderabad'),
    ], validators=[DataRequired()])
    
    destination = SelectField('To', choices=[
        ('Delhi', 'Delhi'),
        ('Mumbai', 'Mumbai'),
        ('Chennai', 'Chennai'),
        ('Bangalore', 'Bangalore'),
        ('Kolkata', 'Kolkata'),
        ('Hyderabad', 'Hyderabad'),
    ], validators=[DataRequired()])
    
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Search')
class TrainSearchForm(FlaskForm):
    origin = StringField('From Station', validators=[DataRequired()])
    destination = StringField('To Station', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Search Trains')
class HotelSearchForm(FlaskForm):
    place = StringField('Place', validators=[DataRequired()])
    date = DateField('Check-in Date', validators=[DataRequired()])
    rooms = IntegerField('Number of Rooms', validators=[DataRequired()])
    submit = SubmitField('Search Hotels')


