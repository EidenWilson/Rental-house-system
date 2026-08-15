import os
from flask import Flask, render_template, request, url_for, redirect, session, flash
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from models import db, User, Property, Booking # Import our new structure
from decorators import login_required, owner_required

load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
# Flask-SQLAlchemy resolves a relative sqlite:/// URI against app.instance_path,
# not the working directory — pin an absolute path so this always points at the
# same rental.db that database.py builds in the project root.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DB_URI = f"sqlite:///{os.path.join(BASE_DIR, 'rental.db')}"

app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-fallback-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', DEFAULT_DB_URI)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- JINJA FILTERS ---
@app.template_filter('dateformat')
def format_datetime(value, format="%b %d, %Y"):
    if not value: return ""
    date_obj = datetime.strptime(value, '%Y-%m-%d')
    return date_obj.strftime(format)

@app.template_filter('currency')
def format_currency(value):
    return f"{value:,.2f}"

# --- ROUTES ---

@app.route('/')
def home():
    query = Property.query

    city = request.args.get('city')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    bedrooms = request.args.get('bedrooms')

    if city:
        query = query.filter(Property.city == city)
    if min_price:
        query = query.filter(Property.price_per_night >= float(min_price))
    if max_price:
        query = query.filter(Property.price_per_night <= float(max_price))
    if bedrooms:
        query = query.filter(Property.num_bedrooms == int(bedrooms))

    properties = query.all()
    return render_template('index.html', properties=properties, filters=request.args)

@app.route('/property/<int:property_id>')
def property_page(property_id):
    prop = db.get_or_404(Property, property_id)
    return render_template('property.html', prop=prop)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'])
        new_user = User(
            username=request.form['username'],
            email=request.form['email'],
            password_hash=hashed_pw,
            user_type=request.form['user_type']
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username or Email already exists.')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session.update({'user_id': user.user_id, 'username': user.username, 'user_type': user.user_type})
            return redirect(url_for('home'))
        flash('Invalid email or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user_type = session['user_type']

    # Get bookings for this renter
    bookings = Booking.query.filter_by(renter_id=user_id).all()

    owner_listings = []
    total_revenue = 0.0
    revenue_by_property = []

    if user_type == 'owner':
        owner_listings = Property.query.filter_by(owner_id=user_id).all()
        # Single scalar total across all of this owner's properties
        total_revenue = db.session.query(db.func.sum(Booking.total_price)).\
            join(Property).filter(Property.owner_id == user_id).scalar() or 0.0
        # Same underlying join, but GROUP BY property to see revenue per listing
        revenue_by_property = db.session.query(
            Property.title, db.func.sum(Booking.total_price)
        ).join(Booking).filter(Property.owner_id == user_id)\
         .group_by(Property.property_id).all()

    return render_template('dashboard.html', bookings=bookings,
                           owner_listings=owner_listings, user_type=user_type,
                           total_revenue=total_revenue,
                           revenue_by_property=revenue_by_property)

@app.route('/book/<int:property_id>', methods=['POST'])
@login_required
def book_property(property_id):
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    d1 = datetime.strptime(start_date, '%Y-%m-%d')
    d2 = datetime.strptime(end_date, '%Y-%m-%d')
    nights = (d2 - d1).days

    if nights <= 0:
        flash('Invalid dates!')
        return redirect(url_for('property_page', property_id=property_id))

    # Interval overlap test: existing.start < new.end AND existing.end > new.start.
    # Dates are stored as ISO 'YYYY-MM-DD' text, which sorts identically to
    # chronological order, so plain string comparison is safe here.
    overlap = Booking.query.filter(
        Booking.property_id == property_id,
        Booking.status == 'confirmed',
        Booking.start_date < end_date,
        Booking.end_date > start_date
    ).first()
    if overlap:
        flash('Those dates are already booked for this property.')
        return redirect(url_for('property_page', property_id=property_id))

    prop = db.session.get(Property, property_id)
    total_price = nights * prop.price_per_night

    new_booking = Booking(renter_id=session['user_id'], property_id=property_id,
                          start_date=start_date,
                          end_date=end_date, total_price=total_price)
    db.session.add(new_booking)
    db.session.commit()
    
    flash(f'Booking confirmed! Total: €{total_price}')
    return redirect(url_for('dashboard'))

# CRUD: Add, Edit, Delete (Condensed for SQLAlchemy)
@app.route('/add_property', methods=['GET', 'POST'])
@owner_required
def add_property():
    if request.method == 'POST':
        try:
            price_per_night = float(request.form['price_per_night'])
            num_bedrooms = int(request.form['num_bedrooms'])
        except ValueError:
            flash('Price and bedrooms must be numbers.')
            return render_template('add_property.html')

        new_prop = Property(
            owner_id=session['user_id'], title=request.form['title'],
            city=request.form['city'], price_per_night=price_per_night,
            num_bedrooms=num_bedrooms, image_url=request.form['image_url'],
            description=request.form['description']
        )
        db.session.add(new_prop)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_property.html')

@app.route('/edit_property/<int:property_id>', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    prop = db.get_or_404(Property, property_id)
    if prop.owner_id != session.get('user_id'): return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            price_per_night = float(request.form['price_per_night'])
            num_bedrooms = int(request.form['num_bedrooms'])
        except ValueError:
            flash('Price and bedrooms must be numbers.')
            return render_template('edit_property.html', prop=prop)

        prop.title = request.form['title']
        prop.city = request.form['city']
        prop.price_per_night = price_per_night
        prop.num_bedrooms = num_bedrooms
        prop.image_url = request.form['image_url']
        prop.description = request.form['description']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_property.html', prop=prop)

@app.route('/delete_property/<int:property_id>', methods=['POST'])
@login_required
def delete_property(property_id):
    prop = db.get_or_404(Property, property_id)
    if prop.owner_id == session.get('user_id'):
        # Delete associated bookings first
        Booking.query.filter_by(property_id=property_id).delete()
        db.session.delete(prop)
        db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Automatically creates the database file and tables
    app.run(debug=True, port=5000)