import sqlite3
from flask import Flask, render_template, request, url_for, redirect, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# JINJA FILTERS (UX Polish)
# Allows you to use {{ date_string | dateformat }} in HTML
@app.template_filter('dateformat')
def format_datetime(value, format="%b %d, %Y"):
    if not value:
        return ""
    from datetime import datetime
    date_obj = datetime.strptime(value, '%Y-%m-%d')
    return date_obj.strftime(format)

@app.template_filter('currency')
def format_currency(value):
    # Ensures price always shows two decimal places
    return f"{value:,.2f}"
# SECURITY CONFIGURATION 
app.secret_key = 'keep_this_secret_and_secure'

DB_NAME = 'rental.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ROUTES

@app.route('/')
def home():
    search_city = request.args.get('city')
    conn = get_db_connection()
    
    if search_city:
        query = "SELECT * FROM Properties WHERE city = ?"
        properties = conn.execute(query, (search_city,)).fetchall()
    else:
        query = "SELECT * FROM Properties"
        properties = conn.execute(query).fetchall()
    
    conn.close()
    return render_template('index.html', properties=properties)

@app.route('/property/<int:property_id>')
def property_page(property_id):
    conn = get_db_connection()
    query = "SELECT * FROM Properties WHERE property_id = ?"
    prop = conn.execute(query, (property_id,)).fetchone()
    conn.close()
    return render_template('property.html', prop=prop)

# REGISTRATION ROUTE 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 1. Get data from the form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']

        # 2. Hash the password
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            # 3. Insert into database
            conn.execute('INSERT INTO Users (username, email, password_hash, user_type) VALUES (?, ?, ?, ?)',
                         (username, email, hashed_password, user_type))
            conn.commit()
            conn.close()
            
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            flash('Username or Email already exists.')
            return redirect(url_for('register'))

    return render_template('register.html')

# LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
        conn.close()

        # Check if user exists AND password matches
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.')

    return render_template('login.html')

# LOGOUT ROUTE 
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# DASHBOARD ROUTE 
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_type = session['user_type']
    conn = get_db_connection()
    
    bookings = []
    owner_listings = []
    total_revenue = 0.0 # Initialize revenue

    # 1. ALWAYS get bookings (since owners can also book)
    booking_query = """
        SELECT Bookings.*, Properties.title, Properties.image_url
        FROM Bookings
        JOIN Properties ON Bookings.property_id = Properties.property_id
        WHERE Bookings.renter_id = ?
    """
    bookings = conn.execute(booking_query, (user_id,)).fetchall()
    
    # 2. ONLY get listings and calculate revenue if owner
    if user_type == 'owner':
        listing_query = "SELECT * FROM Properties WHERE owner_id = ?"
        owner_listings = conn.execute(listing_query, (user_id,)).fetchall()

        # FEATURE ENGINEERING: Calculate Total Revenue
        revenue_query = """
            SELECT SUM(B.total_price) AS total
            FROM Bookings AS B
            JOIN Properties AS P ON B.property_id = P.property_id
            WHERE P.owner_id = ?
        """
        result = conn.execute(revenue_query, (user_id,)).fetchone()
        
        # Ensure result is not None
        total_revenue = result['total'] if result['total'] else 0.0

    conn.close()
    
    # Pass revenue and listings to the template
    return render_template('dashboard.html', 
                           bookings=bookings, 
                           owner_listings=owner_listings,
                           user_type=user_type,
                           total_revenue=total_revenue)

# BOOKING LOGIC 
@app.route('/book/<int:property_id>', methods=['POST'])
def book_property(property_id):
    if 'user_id' not in session:
        flash('Please login to book.')
        return redirect(url_for('login'))
    
    # 1. Get form data
    start_date_str = request.form['start_date']
    end_date_str = request.form['end_date']
    renter_id = session['user_id']
    
    # 2. Calculate number of nights (Feature Engineering!)
    # Convert string dates (2025-11-04) to Python date objects
    d1 = datetime.strptime(start_date_str, '%Y-%m-%d')
    d2 = datetime.strptime(end_date_str, '%Y-%m-%d')
    nights = (d2 - d1).days
    
    if nights <= 0:
        flash('Invalid dates! Check-out must be after Check-in.')
        return redirect(url_for('property_page', property_id=property_id))

    conn = get_db_connection()
    
    # 3. Get property price
    prop = conn.execute('SELECT price_per_night FROM Properties WHERE property_id = ?', (property_id,)).fetchone()
    total_price = nights * prop['price_per_night']
    
    # 4. Save to Database
    conn.execute('INSERT INTO Bookings (renter_id, property_id, start_date, end_date, total_price) VALUES (?, ?, ?, ?, ?)',
                 (renter_id, property_id, start_date_str, end_date_str, total_price))
    conn.commit()
    conn.close()
    
    flash(f'Booking confirmed! Total: €{total_price}')
    return redirect(url_for('dashboard'))

# ADD PROPERTY ROUTE (Data Administration)
@app.route('/add_property', methods=['GET', 'POST'])
def add_property():
    # SECURITY CHECK: Only owners can access this page
    if session.get('user_type') != 'owner':
        flash('Permission denied. Only property owners can add listings.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Get data from the form
        title = request.form['title']
        city = request.form['city']
        price = request.form['price_per_night']
        bedrooms = request.form['num_bedrooms']
        image_url = request.form['image_url']
        description = request.form['description']
        owner_id = session['user_id']
        
        conn = get_db_connection()
        try:
            # Insert new property into the Properties table
            conn.execute('INSERT INTO Properties (owner_id, title, city, price_per_night, num_bedrooms, image_url, description) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         (owner_id, title, city, price, bedrooms, image_url, description))
            conn.commit()
            conn.close()
            
            flash('New property added successfully!')
            return redirect(url_for('home'))
            
        except sqlite3.Error as e:
            flash(f'An error occurred: {e}')
            return redirect(url_for('add_property'))
            
    return render_template('add_property.html')

# EDIT PROPERTY ROUTE (U in CRUD) 
@app.route('/edit_property/<int:property_id>', methods=['GET', 'POST'])
def edit_property(property_id):
    # Security Check 1: Must be an owner to even try
    if session.get('user_type') != 'owner':
        flash('Permission denied. Only owners can edit listings.')
        return redirect(url_for('home'))

    conn = get_db_connection()
    prop = conn.execute('SELECT * FROM Properties WHERE property_id = ?', (property_id,)).fetchone()
    
    # Check 2: Property must exist
    if prop is None:
        flash('Property not found.')
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Security Check 3: Ensure the current user owns the property
    if prop['owner_id'] != session['user_id']:
        flash('You do not have permission to edit this listing.')
        conn.close()
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # --- Handle Saving Changes ---
        title = request.form['title']
        city = request.form['city']
        price = request.form['price_per_night']
        bedrooms = request.form['num_bedrooms']
        image_url = request.form['image_url']
        description = request.form['description']
        
        # Execute UPDATE SQL query to save the changes
        conn.execute("""
            UPDATE Properties SET 
            title = ?, city = ?, price_per_night = ?, num_bedrooms = ?, image_url = ?, description = ?
            WHERE property_id = ?
        """, (title, city, price, bedrooms, image_url, description, property_id))
        
        conn.commit()
        conn.close()
        
        flash('Listing updated successfully!')
        return redirect(url_for('dashboard'))

    conn.close()
    # GET request: Render the form, passing the existing data (prop)
    return render_template('edit_property.html', prop=prop)


# NEW: DELETE PROPERTY ROUTE (D in CRUD) 
@app.route('/delete_property/<int:property_id>', methods=['POST'])
def delete_property(property_id):
    # Security Check 1: Must be an owner
    if session.get('user_type') != 'owner':
        flash('Permission denied. Only owners can delete listings.')
        return redirect(url_for('home'))

    conn = get_db_connection()
    
    # 1. Verify property existence and ownership before deleting
    prop = conn.execute('SELECT owner_id FROM Properties WHERE property_id = ?', (property_id,)).fetchone()
    
    if prop is None:
        flash('Property not found.')
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Security Check 2: Ensure the current user owns the property
    if prop['owner_id'] != session['user_id']:
        flash('You do not have permission to delete this listing.')
        conn.close()
        return redirect(url_for('dashboard'))
    
    # NOTE: To prevent accidental deletion, we require a POST method.
    # We will wrap the actual link in a form in the next step.

    # 2. Execute DELETE SQL query
    conn.execute('DELETE FROM Properties WHERE property_id = ?', (property_id,))
    
    # IMPORTANT: Delete any associated bookings first if not handled by CASCADE
    conn.execute('DELETE FROM Bookings WHERE property_id = ?', (property_id,))
    
    conn.commit()
    conn.close()
    
    flash('Listing successfully deleted.')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
