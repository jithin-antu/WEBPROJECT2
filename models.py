from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from . import db, login_manager
from werkzeug.security import generate_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    newsletter = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    flight_bookings = db.relationship('FlightBooking', backref='user')
    hashed_password = generate_password_hash("admin123")
    
    

# Flight Table
class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flight_no = db.Column(db.String(100), unique=True, nullable=False)
    from_location = db.Column(db.String(100), nullable=False)
    to_location = db.Column(db.String(100), nullable=False)
    departure_time = db.Column(db.String(100))
    arrival_time = db.Column(db.String(100))
    date = db.Column(db.String(100))  # Format: 'YYYY-MM-DD'
    price = db.Column(db.Float)
    seats_available = db.Column(db.Integer)



# Train Table
class Train(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    train_no = db.Column(db.String(10), nullable=False)
    from_station = db.Column(db.String(50), nullable=False)
    to_station = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    departure_time = db.Column(db.String(10), nullable=False)
    arrival_time = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Float, nullable=False)
    seats_available= db.Column(db.Integer, nullable=False)
   

# Hotel Table
class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100)) 
    rooms_available = db.Column(db.Integer, nullable=False)
    price_per_room = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    price_per_night = db.Column(db.Float)

class FlightBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'))
    date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Confirmed')

class TrainBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    train_id = db.Column(db.Integer, db.ForeignKey('train.id'), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    seat_numbers = db.Column(db.String)
    booking_time = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='train_bookings')  # Define here
    train = db.relationship('Train', backref='bookings')
    status = db.Column(db.String(20), default='Confirmed')


class HotelBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    nights = db.Column(db.Integer, nullable=False)
    rooms = db.Column(db.Integer, nullable=False)
    price_per_room = db.Column(db.Float)  # Optional or used elsewhere
    price_per_night = db.Column(db.Float)
    booking_time = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    room_numbers = db.Column(db.String) 

    user = db.relationship('User', backref='hotel_bookings')
    hotel = db.relationship('Hotel', backref='hotel_bookings')
    status = db.Column(db.String(20), default='Confirmed')
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'))  # <== Add this
    seats = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    seat_numbers = db.Column(db.String)
    booking_time = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='bookings')
    flight = db.relationship('Flight', backref='bookings')
    status = db.Column(db.String(20), default='Confirmed')


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5 stars
    comment = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='feedbacks')


