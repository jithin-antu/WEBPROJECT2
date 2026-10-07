from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from datetime import date

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-very-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///roam_easy.db'

    db.init_app(app)
    login_manager.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    # ✅ Create tables and admin user inside app context
    with app.app_context():
        from .models import User
        db.create_all()

        admin_email = 'admin@roameasy.com'
        existing_admin = User.query.filter_by(email=admin_email).first()
        if not existing_admin:
            admin = User(
    first_name="Admin",
    last_name="User",
    email="admin@roameasy.com",
    phone="1234567890",
    password=generate_password_hash("admin123"),
    dob=date(2000, 1, 1),  # ✅ Corrected
    gender="Other",
    address="Admin Street",
    city="Admin City",
    state="Admin State",
    country="India",
    pincode="000000",
    newsletter=False,
    username="admin",
    is_admin=True
)

            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created.")

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))




