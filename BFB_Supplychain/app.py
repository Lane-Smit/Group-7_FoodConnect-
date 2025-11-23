#Cassidy Please make sure our sql code is fine before implementing Authentication
#Dont change the name just the code if needed. 
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'foodconnect-secret-key-bfb321-2025'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('foodconnect.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    """Decorator to require specific role for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('index'))
            if role not in session.get('roles', []):
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

#Our Hompage Route 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

#Our Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            #Get data form form 
            user_fullname = request.form['name']
            email = request.form['email']
            contact_number = request.form['phone']
            password = request.form['password']
            confirm_password = request.form['confirm']

            #Validate passwords match
            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return render_template('signup.html')

            conn = get_db_connection()

            #Check if email already exsists
            existing_user = conn.execute('SELECT email FROM users WHERE email = ?', (email,)).fetchone()
            if existing_user:
                flash('Email already registered. Please login.', 'error')
                conn.close()
                return render_template('signup.html')

            #Create default location for new user
            conn.execute('''
                INSERT INTO locations (province, city, zip_code, street_address)
                VALUES (?, ?, ?, ?)
            ''', ('Not specified', 'Not specified', '0000', 'Not specified'))
            location_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

            #Insert new user
            conn.execute('''
                INSERT INTO users (user_fullname, occupation, location_id, contact_number, email, password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_fullname, '', location_id, contact_number, email, password))

            conn.commit()
            conn.close()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'error')
            return render_template('signup.html')

    return render_template('signup.html')

#Suplier Login Route
@app.route('/supplierlogin', methods=['GET', 'POST'])
def supplier_login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']

            conn = get_db_connection()

            #Validate user credentials
            user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()

            if user:
                #Check if user has Supplier role
                roles = conn.execute('SELECT role FROM user_roles WHERE user_id = ?', (user['user_id'],)).fetchall()
                user_roles = [role['role'] for role in roles]

                #So if user doesn't have Supplier role, add it
                if 'Supplier' not in user_roles:
                    conn.execute('INSERT INTO user_roles (user_id, role) VALUES (?, ?)', (user['user_id'], 'Supplier'))
                    conn.commit()
                    user_roles.append('Supplier')

                #Set sesion
                session['user_id'] = user['user_id']
                session['user_fullname'] = user['user_fullname']
                session['roles'] = user_roles

                conn.close()
                flash('Login successful!', 'success')
                return redirect(url_for('supplier_dashboard'))
            else:
                flash('Invalid email or password.', 'error')
                conn.close()
                return render_template('supplierlogin.html')

        except Exception as e:
            flash(f'Error during login: {str(e)}', 'error')
            return render_template('supplierlogin.html')

    return render_template('supplierlogin.html')

#Recipeint Login Route
@app.route('/recipientlogin', methods=['GET', 'POST'])
def recipient_login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']

            conn = get_db_connection()

            #Validate user credentials
            user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()

            if user:
                #Check if user has Recipient role
                roles = conn.execute('SELECT role FROM user_roles WHERE user_id = ?', (user['user_id'],)).fetchall()
                user_roles = [role['role'] for role in roles]

                #So if user doesn't have Recipient role, add it
                if 'Recipient' not in user_roles:
                    conn.execute('INSERT INTO user_roles (user_id, role) VALUES (?, ?)', (user['user_id'], 'Recipient'))
                    conn.commit()
                    user_roles.append('Recipient')

                #Set sesssion
                session['user_id'] = user['user_id']
                session['user_fullname'] = user['user_fullname']
                session['roles'] = user_roles

                conn.close()
                flash('Login successful!', 'success')
                return redirect(url_for('recipient_dashboard'))
            else:
                flash('Invalid email or password.', 'error')
                conn.close()
                return render_template('recipientlogin.html')

        except Exception as e:
            flash(f'Error during login: {str(e)}', 'error')
            return render_template('recipientlogin.html')

    return render_template('recipientlogin.html')

#Log out Route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

#Supplier Dashboard Route
@app.route('/supplier-dashboard')
@role_required('Supplier')
def supplier_dashboard():
    try:
        user_id = session['user_id']
        conn = get_db_connection()

        #Get KPIs for supplier
        #Total items uploaded
        total_items = conn.execute('SELECT COUNT(*) FROM food_items WHERE user_id = ?', (user_id,)).fetchone()[0]

        #Items expiring soon (within 7 days)
        expiring_soon = conn.execute('''
            SELECT COUNT(*) FROM food_items
            WHERE user_id = ?
            AND date(expiry_date) BETWEEN date('now') AND date('now', '+7 days')
            AND status != 'Completed'
        ''', (user_id,)).fetchone()[0]

        #Donated items (completed transactions)
        donated_today = conn.execute('''
            SELECT COUNT(*) FROM transactions
            WHERE supplier_id = ?
            AND date(created_at) = date('now')
        ''', (user_id,)).fetchone()[0]

        #Active requests for supplier's items
        active_requests = conn.execute('''
            SELECT COUNT(*) FROM requests r
            JOIN food_items f ON r.item_id = f.item_id
            WHERE f.user_id = ? AND r.status = 'Pending'
        ''', (user_id,)).fetchone()[0]

        #Total recipients helped
        recipients_helped = conn.execute('''
            SELECT COUNT(DISTINCT recipient_id) FROM transactions WHERE supplier_id = ?
        ''', (user_id,)).fetchone()[0]

        #Total kg donated
        kg_donated = conn.execute('''
            SELECT COALESCE(SUM(quantity), 0) FROM transactions WHERE supplier_id = ?
        ''', (user_id,)).fetchone()[0]

        #Current inventory
        inventory = conn.execute('''
            SELECT f.*, l.city, l.street_address
            FROM food_items f
            LEFT JOIN locations l ON f.location_id = l.location_id
            WHERE f.user_id = ?
            ORDER BY f.expiry_date ASC
        ''', (user_id,)).fetchall()

        conn.close()

        return render_template('supplier-dashboard.html',
                             total_items=total_items,
                             expiring_soon=expiring_soon,
                             donated_today=donated_today,
                             active_requests=active_requests,
                             recipients_helped=recipients_helped,
                             kg_donated=kg_donated,
                             inventory=inventory)

    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))

#Upload Food Surplus Route
@app.route('/uploadfoodsurplus', methods=['GET', 'POST'])
@role_required('Supplier')
def upload_food_surplus():
    if request.method == 'POST':
        try:
            user_id = session['user_id']

            #Get data form the forms
            food_type = request.form['food_type']
            food_name = request.form['food_name']
            quantity_available = float(request.form['quantity_available'])
            expiry_date = request.form['expiry_date']
            delivery_option = request.form['delivery_option']
            city = request.form['city']
            description = request.form.get('description', '')
            occupation = request.form['occupation']
            contact_number = request.form['contact_number']

            conn = get_db_connection()

            #Update user occupation if provided
            if occupation:
                conn.execute('UPDATE users SET occupation = ? WHERE user_id = ?', (occupation, user_id))

            #Create or get location
            location = conn.execute('SELECT location_id FROM locations WHERE city = ?', (city,)).fetchone()
            if location:
                location_id = location['location_id']
            else:
                conn.execute('''
                    INSERT INTO locations (province, city, zip_code, street_address)
                    VALUES (?, ?, ?, ?)
                ''', ('Not specified', city, '0000', 'Not specified'))
                location_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

            #Insert food item
            conn.execute('''
                INSERT INTO food_items (user_id, food_type, food_name, quantity_available,
                                       expiry_date, delivery_option, location_id, description, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, food_type, food_name, quantity_available, expiry_date,
                  delivery_option, location_id, description, 'Unselected'))

            conn.commit()
            conn.close()

            flash('Food surplus uploaded successfully!', 'success')
            return redirect(url_for('supplier_dashboard'))

        except Exception as e:
            flash(f'Error uploading food surplus: {str(e)}', 'error')
            return render_template('uploadfoodsurplus.html')

    return render_template('uploadfoodsurplus.html')

#View Recipeint needs Route
@app.route('/view-recipient-needs')
@role_required('Supplier')
def view_recipient_needs():
    try:
        user_id = session['user_id']
        conn = get_db_connection()

        #Get all requests for supplier's items
        requests = conn.execute('''
            SELECT r.*, f.food_name, f.food_type, f.quantity_available,
                   u.user_fullname, u.contact_number, u.email
            FROM requests r
            JOIN food_items f ON r.item_id = f.item_id
            JOIN users u ON r.recipient_id = u.user_id
            WHERE f.user_id = ?
            ORDER BY r.created_at DESC
        ''', (user_id,)).fetchall()

        conn.close()

        return render_template('view-recipient-needs.html', requests=requests)

    except Exception as e:
        flash(f'Error loading recipient needs: {str(e)}', 'error')
        return redirect(url_for('supplier_dashboard'))

#Recipient Dashboard Route
@app.route('/recipient-dashboard')
@role_required('Recipient')
def recipient_dashboard():
    try:
        user_id = session['user_id']
        conn = get_db_connection()

        #Get KPIs for recipient
        #Total requests uploaded
        requests_uploaded = conn.execute('SELECT COUNT(*) FROM requests WHERE recipient_id = ?', (user_id,)).fetchone()[0]

        #Total food received (completed transactions)
        kg_received = conn.execute('''
            SELECT COALESCE(SUM(quantity), 0) FROM transactions WHERE recipient_id = ?
        ''', (user_id,)).fetchone()[0]

        #suppliers helped (distinct suppliers)
        suppliers_count = conn.execute('''
            SELECT COUNT(DISTINCT supplier_id) FROM transactions WHERE recipient_id = ?
        ''', (user_id,)).fetchone()[0]

        conn.close()

        return render_template('recipient-dashboard.html',
                             requests_uploaded=requests_uploaded,
                             recipients_supported=suppliers_count,
                             food_received=kg_received)

    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))

#Upload Request Route
@app.route('/uploadrequest', methods=['GET', 'POST'])
@role_required('Recipient')
def upload_request():
    if request.method == 'POST':
        try:
            user_id = session['user_id']

            #Get data from form 
            item_id = int(request.form['item_id'])
            quantity_needed = float(request.form['quantity_needed'])
            urgency_level = request.form.get('urgency_level', 'Medium')

            conn = get_db_connection()

            #Check if quantity needed is available
            food_item = conn.execute('SELECT quantity_available FROM food_items WHERE item_id = ?', (item_id,)).fetchone()

            if not food_item:
                flash('Food item not found.', 'error')
                conn.close()
                return redirect(url_for('view_available_surplus'))

            if quantity_needed > food_item['quantity_available']:
                flash('Requested quantity exceeds available quantity.', 'error')
                conn.close()
                return redirect(url_for('view_available_surplus'))

            #Insert request
            conn.execute('''
                INSERT INTO requests (item_id, recipient_id, quantity_needed, urgency_level, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (item_id, user_id, quantity_needed, urgency_level, 'Pending'))

            conn.commit()
            conn.close()

            flash('Request submitted successfully!', 'success')
            return redirect(url_for('recipient_dashboard'))

        except Exception as e:
            flash(f'Error submitting request: {str(e)}', 'error')
            return redirect(url_for('view_available_surplus'))

    return render_template('uploadrequest.html')

#View Available Surplus Route
@app.route('/view-available-surplus')
@role_required('Recipient')
def view_available_surplus():
    try:
        conn = get_db_connection()

        #Get all available food items
        surplus = conn.execute('''
            SELECT f.*, u.user_fullname, u.contact_number, l.city, l.street_address
            FROM food_items f
            JOIN users u ON f.user_id = u.user_id
            LEFT JOIN locations l ON f.location_id = l.location_id
            WHERE f.status = 'Unselected' AND date(f.expiry_date) >= date('now')
            ORDER BY f.expiry_date ASC
        ''').fetchall()

        conn.close()

        return render_template('view-available-surplus.html', surplus=surplus)

    except Exception as e:
        flash(f'Error loading surplus: {str(e)}', 'error')
        return redirect(url_for('recipient_dashboard'))

#API Endpoint: Get Food Items (JSON)
@app.route('/api/food-items')
def api_food_items():
    try:
        conn = get_db_connection()
        food_items = conn.execute('''
            SELECT f.*, u.user_fullname, l.city
            FROM food_items f
            JOIN users u ON f.user_id = u.user_id
            LEFT JOIN locations l ON f.location_id = l.location_id
            WHERE f.status = 'Unselected'
        ''').fetchall()
        conn.close()

        items_list = [dict(item) for item in food_items]
        return jsonify(items_list)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#API Endpoint: Get Requests (JSON)
@app.route('/api/requests')
def api_requests():
    try:
        conn = get_db_connection()
        requests = conn.execute('''
            SELECT r.*, f.food_name, u.user_fullname
            FROM requests r
            JOIN food_items f ON r.item_id = f.item_id
            JOIN users u ON r.recipient_id = u.user_id
        ''').fetchall()
        conn.close()

        requests_list = [dict(req) for req in requests]
        return jsonify(requests_list)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#API Endpoint: Get KPI Data (JSON)
@app.route('/api/kpi/<user_type>')
@login_required
def api_kpi(user_type):
    try:
        user_id = session['user_id']
        conn = get_db_connection()

        if user_type == 'supplier':
            kpi_data = {
                'total_items': conn.execute('SELECT COUNT(*) FROM food_items WHERE user_id = ?', (user_id,)).fetchone()[0],
                'expiring_soon': conn.execute('''
                    SELECT COUNT(*) FROM food_items
                    WHERE user_id = ? AND date(expiry_date) BETWEEN date('now') AND date('now', '+7 days')
                ''', (user_id,)).fetchone()[0],
                'donated': conn.execute('SELECT COUNT(*) FROM transactions WHERE supplier_id = ?', (user_id,)).fetchone()[0],
                'kg_donated': conn.execute('SELECT COALESCE(SUM(quantity), 0) FROM transactions WHERE supplier_id = ?', (user_id,)).fetchone()[0]
            }
        elif user_type == 'recipient':
            kpi_data = {
                'requests': conn.execute('SELECT COUNT(*) FROM requests WHERE recipient_id = ?', (user_id,)).fetchone()[0],
                'kg_received': conn.execute('SELECT COALESCE(SUM(quantity), 0) FROM transactions WHERE recipient_id = ?', (user_id,)).fetchone()[0],
                'suppliers': conn.execute('SELECT COUNT(DISTINCT supplier_id) FROM transactions WHERE recipient_id = ?', (user_id,)).fetchone()[0]
            }
        else:
            return jsonify({'error': 'Invalid user type'}), 400

        conn.close()
        return jsonify(kpi_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500# API Endpoint: Create Food Item (JSON) - POST
@app.route('/api/food-items/create', methods=['POST'])
@login_required
def api_create_food_item():
    """API endpoint to create a new food surplus item via JSON"""
    try:
        # Check if user has Supplier role
        if 'Supplier' not in session.get('roles', []):
            return jsonify({'error': 'Unauthorized. Supplier role required.'}), 403

        user_id = session['user_id']
        data = request.get_json()

        # Validate required fields
        required_fields = ['food_type', 'food_name', 'quantity_available', 'expiry_date', 'delivery_option', 'city']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        conn = get_db_connection()

        # Create or get location
        location = conn.execute('SELECT location_id FROM locations WHERE city = ?', (data['city'],)).fetchone()
        if location:
            location_id = location['location_id']
        else:
            conn.execute('''
                INSERT INTO locations (province, city, zip_code, street_address)
                VALUES (?, ?, ?, ?)
            ''', ('Not specified', data['city'], '0000', 'Not specified'))
            location_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Insert food item
        cursor = conn.execute('''
            INSERT INTO food_items (user_id, food_type, food_name, quantity_available,
                                   expiry_date, delivery_option, location_id, description, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, data['food_type'], data['food_name'], float(data['quantity_available']),
              data['expiry_date'], data['delivery_option'], location_id,
              data.get('description', ''), 'Unselected'))

        item_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Food item created successfully',
            'item_id': item_id
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Endpoint: Update Request Status (JSON) - PUT/POST
@app.route('/api/requests/update/<int:request_id>', methods=['PUT', 'POST'])
@login_required
def api_update_request(request_id):
    """API endpoint to update a request status via JSON"""
    try:
        data = request.get_json()

        # Validate required field
        if 'status' not in data:
            return jsonify({'error': 'Missing required field: status'}), 400

        # Validate status value
        valid_statuses = ['Pending', 'Selected', 'Completed', 'Cancelled']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400

        conn = get_db_connection()

        # Check if request exists
        existing_request = conn.execute('SELECT * FROM requests WHERE request_id = ?', (request_id,)).fetchone()
        if not existing_request:
            conn.close()
            return jsonify({'error': 'Request not found'}), 404

        # Verify user has permission (either supplier of the item or recipient of the request)
        user_id = session['user_id']
        food_item = conn.execute('SELECT user_id FROM food_items WHERE item_id = ?', (existing_request['item_id'],)).fetchone()

        if user_id != food_item['user_id'] and user_id != existing_request['recipient_id']:
            conn.close()
            return jsonify({'error': 'Unauthorized. You can only update your own requests or requests for your items.'}), 403

        # Update request status
        conn.execute('UPDATE requests SET status = ? WHERE request_id = ?', (data['status'], request_id))
        conn.commit()

        # Get updated request
        updated_request = conn.execute('''
            SELECT r.*, f.food_name, u.user_fullname
            FROM requests r
            JOIN food_items f ON r.item_id = f.item_id
            JOIN users u ON r.recipient_id = u.user_id
            WHERE r.request_id = ?
        ''', (request_id,)).fetchone()

        conn.close()

        return jsonify({
            'success': True,
            'message': 'Request updated successfully',
            'request': dict(updated_request)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Windows workaround: avoid Unicode errors in hostname resolution
    import socket

    original_getfqdn = socket.getfqdn

    def safe_getfqdn(name=''):
        try:
            return original_getfqdn(name)
        except UnicodeDecodeError:
            # Fallback if Windows returns a weird hostname
            return 'localhost'

    socket.getfqdn = safe_getfqdn

    app.run(host='127.0.0.1', port=5000, debug=True)
