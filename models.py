from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    user_type = db.Column(db.String, nullable=False, default='renter')

class Property(db.Model):
    __tablename__ = 'Properties'
    property_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.Text)
    city = db.Column(db.String, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    num_bedrooms = db.Column(db.Integer)
    image_url = db.Column(db.String)

class Booking(db.Model):
    __tablename__ = 'Bookings'
    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    renter_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('Properties.property_id'), nullable=False)
    start_date = db.Column(db.String, nullable=False)
    end_date = db.Column(db.String, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, nullable=False, default='confirmed')