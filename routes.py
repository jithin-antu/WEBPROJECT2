from flask import render_template, redirect, url_for, flash, request,session
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User
from .forms import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint
from app.forms import FlightSearchForm,TrainSearchForm,HotelSearchForm
from functools import wraps
from app.forms import LoginForm
from datetime import datetime
from app.models import Flight
from app.models import Train
from app.models import Hotel
from .models import Booking,TrainBooking,HotelBooking,Feedback
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_required, current_user
from app.utils import generate_qr_code


from flask import jsonify
main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__)
@main.route('/')
def home():
    return render_template('home.html')

def generate_seat_numbers(flight_id, count):
    rows = 30
    cols = ['A', 'B', 'C', 'D', 'E', 'F']

    existing_bookings = Booking.query.filter_by(flight_id=flight_id).all()
    booked = set()
    for b in existing_bookings:
        if b.seat_numbers:
            booked.update(b.seat_numbers.split(','))

    available = []
    for r in range(1, rows + 1):
        for c in cols:
            seat = f"{c}{r}"
            if seat not in booked:
                available.append(seat)
            if len(available) == count:
                return available

    raise Exception("Not enough available seats")

def generate_train_seat_numbers(train_id, count):
    max_seats = 80  # Customize based on your train configuration
    prefix = 'S'    # All seats will be S1, S2, ..., S80

    # Get already booked seats for this train
    existing = TrainBooking.query.filter_by(train_id=train_id).all()
    booked = set()
    for booking in existing:
        if booking.seat_numbers:
            booked.update(booking.seat_numbers.split(','))

    # Generate available seat numbers
    available = []
    for i in range(1, max_seats + 1):
        seat = f"{prefix}{i}"
        if seat not in booked:
            available.append(seat)
        if len(available) == count:
            return available

    raise Exception("Not enough seats available")

@main.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        dob = datetime.strptime(request.form['dob'], '%Y-%m-%d').date()
        gender = request.form['gender']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        pincode = request.form['pincode']
        terms = request.form.get('terms')
        newsletter = True if request.form.get('newsletter') else False

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for('main.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "error")
            return redirect(url_for('main.register'))

        hashed_password = generate_password_hash(password)

        new_user = User(
    first_name=first_name,
    last_name=last_name,
    username=username,  # <== ✅ MUST include this
    email=email,
    phone=phone,
    password=hashed_password,
    dob=dob,
    gender=gender,
    address=address,
    city=city,
    state=state,
    country=country,
    pincode=pincode,
    newsletter=newsletter,
    is_admin=False
)


        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('main.login'))

    # ✅ THIS is what was missing (pass the form to the template):
    return render_template('register.html')


from werkzeug.security import check_password_hash

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.first_name
            session['is_admin'] = getattr(user, 'is_admin', False)

            flash('Login successful!', 'success')

            if session['is_admin']:
                return redirect(url_for('main.admin_dashboard'))  # redirect admin
            else:
                return redirect(url_for('main.home'))  # redirect normal user
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('main.login'))

    # Only render the template if the form was not submitted or invalid
    return render_template('login.html', form=form)



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to view this page.', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function
@main.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.login'))

@main.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in first.", "warning")
        return redirect(url_for('main.login'))

    user = User.query.get(user_id)
    if not user:
        flash("User not found. Please log in again.", "danger")
        session.clear()
        return redirect(url_for('main.login'))

    bookings = Booking.query.filter_by(user_id=user.id).join(Flight).all()
    train_bookings = TrainBooking.query.filter_by(user_id=user.id).join(Train).all()
    hotel_bookings = HotelBooking.query.filter_by(user_id=user.id).join(Hotel).all()

    return render_template('profile.html', user=user, bookings=bookings, train_bookings=train_bookings, hotel_bookings=hotel_bookings)

@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.email = request.form['email']
        user.phone = request.form['phone']
        user.address = request.form['address']

        new_password = request.form['password']
        if new_password.strip():  # Only update if user provided a password
            user.password = generate_password_hash(new_password)

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for('main.profile'))

    return render_template('edit_profile.html', user=user)





@main.route('/search_flight', methods=['GET', 'POST'])
@login_required
def search_flight():
    form = FlightSearchForm()
    results = []

    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        date_obj = form.date.data

        # Convert to 'YYYY-MM-DD' format
        if date_obj:
            date = date_obj.strftime('%Y-%m-%d')
        else:
            date = None

        if origin and destination and date:
            # Query DB with exact match
            results = Flight.query.filter_by(
                from_location=origin,
                to_location=destination,
                date=date
            ).all()
            return render_template('flight_results.html', results=results)

            if not results:
                flash("No flights found for the selected criteria.", "danger")
        else:
            flash("Please select all fields.", "warning")

    return render_template('search_flight.html', form=form, results=results)
@main.route('/book_flight/<int:flight_id>', methods=['GET', 'POST'])
@login_required
def book_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)

    if request.method == 'POST':
        seats = int(request.form.get('seats'))
        if seats <= 0:
            flash("Please select at least 1 seat.", "warning")
            return redirect(request.url)

        if seats > flight.seats_available:
            flash("Not enough seats available.", "danger")
            return redirect(request.url)

        # Calculate total
        total = seats * flight.price
        seat_numbers = generate_seat_numbers(flight.id, seats)
        # Temporarily store booking info in session
        session['booking'] = {
            'flight_id': flight.id,
            'seats': seats,
            'total': total,
            'seat_numbers': seat_numbers

        }

        return redirect(url_for('main.payment'))

    return render_template('book_flight.html', flight=flight)

@main.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    booking_data = session.get('booking')

    if not booking_data:
        flash("No booking data found. Please search and select a flight again.", "danger")
        return redirect(url_for('main.search_flight'))

    flight = Flight.query.get_or_404(booking_data['flight_id'])
    seats = booking_data['seats']
    bill = booking_data['total']

    if request.method == 'POST':
        # ✅ Fix: Get user_id from session
        user_id = session.get('user_id')
        if not user_id:
            flash("User not logged in.", "danger")
            return redirect(url_for('main.login'))

        # Save booking to DB
        new_booking = Booking(
            user_id=user_id,
            flight_id=flight.id,
            seats=seats,
            amount=bill,
            booking_time=datetime.utcnow(),
            seat_numbers=','.join(booking_data['seat_numbers'])
        )
        db.session.add(new_booking)

        # Reduce available seats
        flight.seats_available -= seats
        db.session.commit()

        # Clear session booking
        session.pop('booking', None)

        flash("Payment successful! Your booking has been confirmed.", "success")
        return redirect(url_for('main.view_ticket', type='flight', booking_id=new_booking.id))

    return render_template('payment.html', flight=flight, bill=bill)


@main.route('/search/train', methods=['GET', 'POST'])
@login_required
def search_train():
    from_station_list = [row[0] for row in db.session.query(Train.from_station).distinct().all()]
    to_station_list = [row[0] for row in db.session.query(Train.to_station).distinct().all()]

    if request.method == 'POST':
        origin = request.form['from_station']
        destination = request.form['to_station']
        date = request.form['date']
        results = Train.query.filter_by(from_station=origin, to_station=destination, date=date).all()
        return render_template('train_results.html', results=results)

    return render_template('search_train.html',
                           from_stations=from_station_list,
                           to_stations=to_station_list)

    return render_template('search_train.html', form=form)
@main.route('/book_train/<int:train_id>', methods=['GET', 'POST'])
@login_required
def book_train(train_id):
    train = Train.query.get_or_404(train_id)

    if request.method == 'POST':
        seats_requested = int(request.form.get('seats'))

        if seats_requested <= 0 or seats_requested > train.seats_available:
            flash('Invalid number of seats selected.', 'error')
            return redirect(url_for('main.book_train', train_id=train.id))
        seat_numbers = [f"T{train.id}-{i+1}" for i in range(seats_requested)]
        # Store booking details in session
        session['train_booking'] = {
            'train_id': train.id,
            'seats': seats_requested,
            'total_amount': train.price * seats_requested,
            'seat_numbers': [f"T{train.id}-{i+1}" for i in range(seats_requested)]
        }

        return redirect(url_for('main.train_payment'))

    return render_template('book_train.html', train=train)

@main.route('/payment/train', methods=['GET', 'POST'])
@login_required
def train_payment():
    booking = session.get('train_booking')
    data = session.get('train_booking_data')

    if not booking:
        flash("No train booking in progress.", "error")
        return redirect(url_for('main.search_train'))

    train = Train.query.get_or_404(booking['train_id'])
    if request.method == 'POST':
        # ✅ Fix: Get user_id from session
        user_id = session.get('user_id')
    if request.method == 'POST':
        seats = booking['seats']
        if seats > train.seats_available:
            flash("Not enough seats available.", "error")
            return redirect(url_for('main.book_train', train_id=train.id))

        train.seats_available -= seats

        new_booking = TrainBooking(
            user_id = user_id,
            train_id=train.id,
            seats=seats,
           seat_numbers=','.join(booking['seat_numbers']),
            amount=booking['total_amount']
        )
        db.session.add(new_booking)
        db.session.commit()

        session.pop('train_booking', None)
        flash("Train booking successful!", "success")
        return redirect(url_for('main.view_ticket', type='train', booking_id=new_booking.id))

    return render_template('payment_train.html', train=train, booking=booking)


@main.route('/search_hotels', methods=['GET', 'POST'])
def search_hotels():
    locations = db.session.query(Hotel.location).distinct().all()
    locations = [loc[0] for loc in locations]

    # Build location → list of cities
    location_to_cities = {}
    for loc in locations:
        cities = db.session.query(Hotel.city).filter(Hotel.location == loc).distinct().all()
        location_to_cities[loc] = [city[0] for city in cities]

    if request.method == 'POST':
        selected_location = request.form['location']
        selected_city = request.form['city']
        date = request.form['date']
        rooms = int(request.form['rooms'])

        hotels = Hotel.query.filter(
            Hotel.location == selected_location,
            Hotel.city == selected_city,
            Hotel.rooms_available >= rooms
        ).all()

        return render_template(
            'hotel_results.html',
            hotels=hotels,
            location=selected_location,
            city=selected_city,
            date=date,
            rooms=rooms
        )

    return render_template(
        'search_hotel.html',
        locations=locations,
        location_to_cities=location_to_cities
    )

@main.route('/book/hotel/<int:hotel_id>/<int:rooms>', methods=['GET', 'POST'])
@login_required
def book_hotel(hotel_id, rooms):
    hotel = Hotel.query.get_or_404(hotel_id)

    if request.method == 'POST':
        nights = int(request.form['nights'])
        return redirect(url_for('main.hotel_payment', hotel_id=hotel_id, rooms=rooms, nights=nights))

    return render_template('book_hotel.html', hotel=hotel, rooms=rooms)




@main.route('/payment/hotel/<int:hotel_id>/<int:rooms>/<int:nights>', methods=['GET', 'POST'])
@login_required
def hotel_payment(hotel_id, rooms, nights):
    hotel = Hotel.query.get_or_404(hotel_id)
    user_id = session.get('user_id')
    amount = (hotel.price_per_night * nights) + (rooms * hotel.price_per_room)
    assigned_rooms = [f"R{hotel_id:03d}-{i+1}" for i in range(rooms)]  # e.g., R007-1, R007-2
    if request.method == 'POST':
        booking = HotelBooking(
            user_id=user_id,
            hotel_id=hotel.id,
            nights=nights,
            rooms=rooms,
            room_numbers=", ".join(assigned_rooms),
            amount=amount
        )
        db.session.add(booking)
        hotel.rooms_available -= rooms
        db.session.commit()

        flash('Hotel booking successful!', 'success')
        return redirect(url_for('main.view_ticket', type='hotel', booking_id=booking.id))
    return render_template('hotel_payment.html', hotel=hotel, rooms=rooms, nights=nights, amount=amount)




@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/contact')
def contact():
    return render_template('contact.html')


@main.route('/cancel_flight/<int:booking_id>')
@login_required
def cancel_flight(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id == session['user_id']:
        booking.status = 'Cancelled'
        db.session.commit()
        flash('Flight booking cancelled.', 'success')
    return redirect(url_for('main.profile'))

@main.route('/cancel_train/<int:booking_id>')
@login_required
def cancel_train(booking_id):
    booking = TrainBooking.query.get_or_404(booking_id)
    if booking.user_id == session['user_id']:
        booking.status = 'Cancelled'
        db.session.commit()
        flash('Train booking cancelled.', 'success')
    return redirect(url_for('main.profile'))

@main.route('/cancel_hotel/<int:booking_id>')
@login_required
def cancel_hotel(booking_id):
    booking = HotelBooking.query.get_or_404(booking_id)
    if booking.user_id == session['user_id']:
        booking.status = 'Cancelled'
        db.session.commit()
        flash('Hotel booking cancelled.', 'success')
    return redirect(url_for('main.profile'))




def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            flash("Access denied.", "danger")
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Dashboard

@main.route('/admin')
@admin_required
def admin_dashboard():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('main.home'))

    return render_template('admin/dashboard.html')

# ---------------------- Flights --------------------------
@main.route('/admin/flights')
@admin_required
def admin_flights():
    flights = Flight.query.all()
    print("Fetched Flights:", flights)  # 👈 debug
    return render_template('admin/admin_flights.html', flights=flights)



@main.route('/admin/add_flight', methods=['GET', 'POST'])
@admin_required
def add_flight():
    if request.method == 'POST':
        flight = Flight(
            flight_no=request.form['flight_no'],
            from_location=request.form['from_location'],
            to_location=request.form['to_location'],
            departure_time=request.form['departure_time'],
            arrival_time=request.form['arrival_time'],
            date=request.form['date'],
            price=request.form['price'],
            seats_available=request.form['seats_available']
        )
        db.session.add(flight)
        db.session.commit()
        flash('Flight added successfully!', 'success')
        return redirect(url_for('main.admin_flights'))
    return render_template('admin/add_flight.html')

@main.route('/admin/edit_flight/<int:flight_id>', methods=['GET', 'POST'])
@admin_required
def edit_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)

    if request.method == 'POST':
        flight.flight_no = request.form.get('flight_no')
        flight.from_location = request.form.get('from_location')
        flight.to_location = request.form.get('to_location')
        flight.departure_time = request.form.get('departure_time')
        flight.arrival_time = request.form.get('arrival_time')
        flight.date = request.form.get('date')
        flight.price = request.form.get('price')
        flight.seats_available = request.form.get('seats_available')

        db.session.commit()
        flash('Flight updated successfully!', 'success')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('admin/edit_flight.html', flight=flight)


@main.route('/admin/delete_flight/<int:flight_id>')
@admin_required
def delete_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    db.session.delete(flight)
    db.session.commit()
    flash('Flight deleted successfully.', 'success')
    return redirect(url_for('main.admin_flights'))


# ---------------- Train Management ----------------

@main.route('/admin/trains')
@login_required
def admin_trains():
    if not session.get("is_admin"):
        flash("Access denied.", "danger")
        return redirect(url_for("main.home"))
    
    trains = Train.query.all()
    return render_template("admin/admin_trains.html", trains=trains)

@main.route('/admin/add_train', methods=['GET', 'POST'])
@admin_required
def add_train():
    if request.method == 'POST':
        train_no = request.form['train_no']
        from_station = request.form['from_station']
        to_station = request.form['to_station']
        departure_time = request.form['departure_time']
        arrival_time = request.form['arrival_time']
        date_val = request.form['date']
        price = request.form['price']
        seats_available = request.form['seats_available']

        train = Train(
            train_no=train_no,
            from_station=from_station,
            to_station=to_station,
            departure_time=departure_time,
            arrival_time=arrival_time,
            date=date_val,
            price=price,
            seats_available=seats_available
        )
        db.session.add(train)
        db.session.commit()
        flash("Train added successfully!", "success")
        return redirect(url_for('main.admin_trains'))

    return render_template('admin/add_train.html')

@main.route('/admin/edit_train/<int:train_id>', methods=['GET', 'POST'])
@admin_required
def edit_train(train_id):
    train = Train.query.get_or_404(train_id)
    
    if request.method == 'POST':
        train.train_no = request.form['train_no']
        train.from_station = request.form['from_station']
        train.to_station = request.form['to_station']
        train.departure_time = request.form['departure_time']
        train.arrival_time = request.form['arrival_time']
        train.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        train.price = request.form['price']
        train.seats_available = request.form['seats_available']
        db.session.commit()
        flash('Train updated successfully!', 'success')
        return redirect(url_for('main.admin_trains'))

    return render_template('admin/edit_train.html', train=train)


@main.route('/admin/delete_train/<int:train_id>', methods=['POST'])
@login_required
def delete_train(train_id):
    if not session.get("is_admin"):
        flash("Access denied.", "danger")
        return redirect(url_for("main.home"))

    train = Train.query.get_or_404(train_id)
    db.session.delete(train)
    db.session.commit()
    flash('Train deleted successfully.', 'success')
    return redirect(url_for('admin/admin_trains.html'))

# ---------------- Hotel Management ----------------

@main.route('/admin/hotels')
@login_required
def admin_hotels():
    if not session.get("is_admin"):
        flash("Access denied.", "danger")
        return redirect(url_for("main.home"))
    
    hotels = Hotel.query.all()
    return render_template("admin/admin_hotels.html", hotels=hotels)

@main.route('/admin/add_hotel', methods=['GET', 'POST'])
@login_required
def add_hotel():
    if not session.get("is_admin"):
        flash("Access denied.", "danger")
        return redirect(url_for("main.home"))

    if request.method == 'POST':
        hotel = Hotel(
            name=request.form['name'],
            location=request.form['location'],
            city=request.form['city'],

            rooms_available=int(request.form['rooms_available']),
            price_per_room=float(request.form['price_per_room']),
            date=request.form['date'],
            price_per_night=float(request.form['price_per_night'])
        )
        db.session.add(hotel)
        db.session.commit()
        flash('Hotel added successfully.', 'success')
        return redirect(url_for('admin/admin_hotels.html'))

    return render_template('admin/add_hotel.html')

from datetime import datetime

@main.route('/admin/edit_hotel/<int:hotel_id>', methods=['GET', 'POST'])
@admin_required
def edit_hotel(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    if request.method == 'POST':
        hotel.name = request.form['name']
        hotel.location = request.form['location']
        hotel.city = request.form['city']
        hotel.price_per_room = request.form.get('price_per_room')
        hotel.price_per_night = request.form.get('price_per_night')
        hotel.rooms_available = request.form['rooms_available']
        db.session.commit()
        flash('Hotel updated successfully!', 'success')
        return redirect(url_for('main.admin_hotels'))
    return render_template('admin/edit_hotel.html', hotel=hotel)


@main.route('/admin/delete_hotel/<int:hotel_id>', methods=['POST'])
@login_required
def delete_hotel(hotel_id):
    if not session.get("is_admin"):
        flash("Access denied.", "danger")
        return redirect(url_for("main.home"))

    hotel = Hotel.query.get_or_404(hotel_id)
    db.session.delete(hotel)
    db.session.commit()
    flash('Hotel deleted successfully.', 'success')
    return redirect(url_for('main.admin_hotels'))

@main.route('/admin/flights')
def manage_flights():
    flights = Flight.query.all()
    return render_template('admin/admin_flights.html', flights=flights)

@main.route('/admin/trains')
def manage_trains():
    trains = Train.query.all()
    return render_template('admin/admin_trains.html', trains=trains)

@main.route('/admin/hotels')
def manage_hotels():
    hotels = Hotel.query.all()
    return render_template('admin/admin_hotels.html', hotels=hotels)

from flask_login import login_required, current_user

@main.route('/feedback', methods=['GET', 'POST'])

def feedback():
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        user_id = session['user_id']  # ✅ Get user_id from session

        feedback = Feedback(
            user_id=user_id,
            rating=rating,
            comment=comment
        )
        db.session.add(feedback)
        db.session.commit()
        flash("Thanks for your feedback!", "success")
        return redirect(url_for('main.home'))
   
    return render_template('feedback.html')



@main.route('/admin/feedbacks')
@admin_required  # make sure this decorator checks is_admin
def admin_feedbacks():
    feedbacks = Feedback.query.order_by(Feedback.timestamp.desc()).all()
    return render_template('admin/admin_feedback.html', feedbacks=feedbacks)

@main.route('/admin/analytics')
@admin_required  # if you have one to protect admin routes
def admin_analytics():
    from app.models import Booking, TrainBooking, HotelBooking  # adjust as needed
    total_flight_bookings = Booking.query.count()
    total_train_bookings = TrainBooking.query.count()
    total_hotel_bookings = HotelBooking.query.count()

    total_revenue = (
        db.session.query(db.func.sum(Booking.amount)).scalar() or 0
    ) + (
        db.session.query(db.func.sum(TrainBooking.amount)).scalar() or 0
    ) + (
        db.session.query(db.func.sum(HotelBooking.amount)).scalar() or 0
    )

    return render_template('admin/analytics.html',
        total_flight_bookings=total_flight_bookings,
        total_train_bookings=total_train_bookings,
        total_hotel_bookings=total_hotel_bookings,
        total_revenue=total_revenue
    )

@main.route('/ticket/<string:type>/<int:booking_id>')

def view_ticket(type, booking_id):
    user_id = session.get('user_id')

    if type == 'hotel':
        booking = HotelBooking.query.get_or_404(booking_id)
        if booking.user_id != user_id:
            abort(403)
        hotel = Hotel.query.get(booking.hotel_id)
        qr_data = f"Hotel Booking | ID: {booking.id} | {hotel.name}, {hotel.location} | Nights: {booking.nights} | Rooms: {booking.rooms} | Amount: ₹{booking.amount}"
        qr_img = generate_qr_code(qr_data)
        return render_template('ticket_hotel.html', booking=booking, hotel=hotel, qr_img=qr_img)

    elif type == 'flight':
        booking = Booking.query.get_or_404(booking_id)
        if booking.user_id != user_id:
            abort(403)
        flight = Flight.query.get(booking.flight_id)
        qr_data = f"Flight Booking | ID: {booking.id} | Flight: {flight.flight_no} | From: {flight.from_location} | To: {flight.to_location} | Date: {flight.date} | Amount: ₹{booking.amount}"
        qr_img = generate_qr_code(qr_data)
        return render_template('ticket_flight.html', booking=booking, flight=flight, qr_img=qr_img)

    elif type == 'train':
        booking = TrainBooking.query.get_or_404(booking_id)
        if booking.user_id != user_id:
            abort(403)
        train = Train.query.get(booking.train_id)
        qr_data = f"Train Booking | ID: {booking.id} | Train: {train.train_no} | From: {train.from_station} | To: {train.to_station} | Date: {train.date} | Amount: ₹{booking.amount}"
        qr_img = generate_qr_code(qr_data)
        return render_template('ticket_train.html', booking=booking, train=train, qr_img=qr_img)

    else:
        abort(404)

@main.route('/admin/users')

def manage_users():
    if not session.get("is_admin"):  # your own is_admin() check
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.index'))

    users = User.query.filter(User.is_admin == False).all()
    return render_template('admin/manage_users.html', users=users)
@main.route('/admin/delete_user/<int:user_id>', methods=['POST'])

def delete_user(user_id):
    if not session.get("is_admin"):
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully", "success")
    return redirect(url_for('main.manage_users'))

@main.route('/admin/add_user', methods=['GET', 'POST'])

def add_user():
    if not session.get("is_admin"):
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        dob = datetime.strptime(request.form['dob'], '%Y-%m-%d').date()
        gender = request.form['gender']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        pincode = request.form['pincode']

        if User.query.filter_by(email=email).first():
            flash("Email already exists", "warning")
            return redirect(url_for('main.add_user'))
        hashed_password = generate_password_hash(password)
        user = User(first_name=first_name,
        last_name=last_name,
        username=username,  # <== ✅ MUST include this
        email=email,
        phone=phone,
        password=hashed_password,
        dob=dob,
        gender=gender,
        address=address,
        city=city,
        state=state,
        country=country,
        pincode=pincode,
        
        is_admin=False)
        db.session.add(user)
        db.session.commit()
        flash("User added successfully", "success")
        return redirect(url_for('main.manage_users'))

    return render_template('admin/add_user.html')

@main.route('/admin/bookings')
def view_all_bookings():
    return render_template('admin/all_bookings.html')


@main.route('/admin/bookings/flights')
def view_flightbooking():
    user_id = request.args.get('user_id', type=int)
    date = request.args.get('date')

    flight_bookings = Booking.query
    if user_id:
        flight_bookings = flight_bookings.filter_by(user_id=user_id)
    if date:
        flight_bookings = flight_bookings.join(Flight).filter(Flight.date == date)

    return render_template('admin/flight_bookings.html', flight_bookings=flight_bookings.all())


@main.route('/admin/bookings/trains')
def view_trainbooking():
    user_id = request.args.get('user_id', type=int)
    date = request.args.get('date')

    train_bookings = TrainBooking.query
    if user_id:
        train_bookings = train_bookings.filter_by(user_id=user_id)
    if date:
        train_bookings = train_bookings.join(Train).filter(Train.date == date)

    return render_template('admin/train_bookings.html', train_bookings=train_bookings.all())


@main.route('/admin/bookings/hotels')
def view_hotelbooking():
    user_id = request.args.get('user_id', type=int)

    hotel_bookings = HotelBooking.query
    if user_id:
        hotel_bookings = hotel_bookings.filter_by(user_id=user_id)

    return render_template('admin/hotel_bookings.html', hotel_bookings=hotel_bookings.all())
