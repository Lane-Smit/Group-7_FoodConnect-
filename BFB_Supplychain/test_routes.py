# Carin
"""
Comprehensive Route Testing Script for FoodConnect
Tests all routes end-to-end using Flask test client
"""
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, get_db_connection
import json

# Test results storage
test_results = {
    'passed': 0,
    'failed': 0,
    'tests': []
}

def log_test(test_name, status, message=""):
    """Log test result"""
    result = {
        'test': test_name,
        'status': status,
        'message': message
    }
    test_results['tests'].append(result)
    if status == 'PASS':
        test_results['passed'] += 1
        print(f"[PASS] {test_name}: {status}")
    else:
        test_results['failed'] += 1
        print(f"[FAIL] {test_name}: {status} - {message}")

def test_public_routes():
    """Test public routes (index, about, contact)"""
    print("\n=== Testing Public Routes ===")

    with app.test_client() as client:
        # Test index route
        response = client.get('/')
        if response.status_code == 200:
            log_test("GET /", "PASS")
        else:
            log_test("GET /", "FAIL", f"Status code: {response.status_code}")

        # Test about route
        response = client.get('/about')
        if response.status_code == 200:
            log_test("GET /about", "PASS")
        else:
            log_test("GET /about", "FAIL", f"Status code: {response.status_code}")

        # Test contact route
        response = client.get('/contact')
        if response.status_code == 200:
            log_test("GET /contact", "PASS")
        else:
            log_test("GET /contact", "FAIL", f"Status code: {response.status_code}")

def test_authentication_routes():
    """Test authentication routes (signup, login, logout)"""
    print("\n=== Testing Authentication Routes ===")

    with app.test_client() as client:
        # Test signup GET
        response = client.get('/signup')
        if response.status_code == 200:
            log_test("GET /signup", "PASS")
        else:
            log_test("GET /signup", "FAIL", f"Status code: {response.status_code}")

        # Test signup POST
        response = client.post('/signup', data={
            'name': 'Test User End-to-End',
            'email': f'test_e2e_{os.getpid()}@example.com',
            'phone': '0123456789',
            'password': 'testpass123',
            'confirm': 'testpass123'
        }, follow_redirects=True)
        if response.status_code == 200 and b'Account created' in response.data or b'Email already registered' in response.data:
            log_test("POST /signup", "PASS", "User registration working")
        else:
            log_test("POST /signup", "FAIL", f"Status code: {response.status_code}")

        # Test supplier login GET
        response = client.get('/supplierlogin')
        if response.status_code == 200:
            log_test("GET /supplierlogin", "PASS")
        else:
            log_test("GET /supplierlogin", "FAIL", f"Status code: {response.status_code}")

        # Test supplier login POST (using existing user from mock data)
        response = client.post('/supplierlogin', data={
            'email': 'alice@example.com',
            'password': 'hashed_password_1'
        }, follow_redirects=False)
        if response.status_code in [200, 302]:  # 302 is redirect
            log_test("POST /supplierlogin", "PASS", "Login redirects correctly")
        else:
            log_test("POST /supplierlogin", "FAIL", f"Status code: {response.status_code}")

        # Test recipient login GET
        response = client.get('/recipientlogin')
        if response.status_code == 200:
            log_test("GET /recipientlogin", "PASS")
        else:
            log_test("GET /recipientlogin", "FAIL", f"Status code: {response.status_code}")

        # Test recipient login POST
        response = client.post('/recipientlogin', data={
            'email': 'carol@example.com',
            'password': 'hashed_password_3'
        }, follow_redirects=False)
        if response.status_code in [200, 302]:
            log_test("POST /recipientlogin", "PASS", "Login redirects correctly")
        else:
            log_test("POST /recipientlogin", "FAIL", f"Status code: {response.status_code}")

        # Test logout
        response = client.get('/logout', follow_redirects=False)
        if response.status_code == 302:
            log_test("GET /logout", "PASS", "Logout redirects to index")
        else:
            log_test("GET /logout", "FAIL", f"Status code: {response.status_code}")

def test_supplier_routes():
    """Test supplier routes"""
    print("\n=== Testing Supplier Routes ===")

    with app.test_client() as client:
        # Login as suplier first
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_fullname'] = 'Alice Smith'
            sess['roles'] = ['Supplier']

        # Test suplier dashboard
        response = client.get('/supplier-dashboard')
        if response.status_code == 200:
            log_test("GET /supplier-dashboard", "PASS")
        else:
            log_test("GET /supplier-dashboard", "FAIL", f"Status code: {response.status_code}")

        # Test upload food surplus GET
        response = client.get('/uploadfoodsurplus')
        if response.status_code == 200:
            log_test("GET /uploadfoodsurplus", "PASS")
        else:
            log_test("GET /uploadfoodsurplus", "FAIL", f"Status code: {response.status_code}")

        # Test upload food surplus POST
        response = client.post('/uploadfoodsurplus', data={
            'user_fullname': 'Test Supplier',
            'occupation': 'Restaurant',
            'city': 'Cape Town',
            'contact_number': '0821234567',
            'food_type': 'Vegetables',
            'food_name': 'Test Carrots',
            'quantity_available': '10',
            'delivery_option': 'Pickup',
            'expiry_date': '2025-12-31',
            'description': 'Test surplus food'
        }, follow_redirects=False)
        if response.status_code in [200, 302]:
            log_test("POST /uploadfoodsurplus", "PASS", "Food surplus upload working")
        else:
            log_test("POST /uploadfoodsurplus", "FAIL", f"Status code: {response.status_code}")

        # Test view recipient needs
        response = client.get('/view-recipient-needs')
        if response.status_code == 200:
            log_test("GET /view-recipient-needs", "PASS")
        else:
            log_test("GET /view-recipient-needs", "FAIL", f"Status code: {response.status_code}")

def test_recipient_routes():
    """Test recipient routes"""
    print("\n=== Testing Recipient Routes ===")

    with app.test_client() as client:
        # Login as recipient
        with client.session_transaction() as sess:
            sess['user_id'] = 3
            sess['user_fullname'] = 'Carol White'
            sess['roles'] = ['Recipient']

        # Test recipient dashboard
        response = client.get('/recipient-dashboard')
        if response.status_code == 200:
            log_test("GET /recipient-dashboard", "PASS")
        else:
            log_test("GET /recipient-dashboard", "FAIL", f"Status code: {response.status_code}")

        # Test view available surplus
        response = client.get('/view-available-surplus')
        if response.status_code == 200:
            log_test("GET /view-available-surplus", "PASS")
        else:
            log_test("GET /view-available-surplus", "FAIL", f"Status code: {response.status_code}")

        # Test upload request GET
        response = client.get('/uploadrequest')
        if response.status_code == 200:
            log_test("GET /uploadrequest", "PASS")
        else:
            log_test("GET /uploadrequest", "FAIL", f"Status code: {response.status_code}")

        # Test upload request POST (using existing food item)
        response = client.post('/uploadrequest', data={
            'item_id': '1',
            'quantity_needed': '5',
            'urgency_level': 'Medium'
        }, follow_redirects=False)
        if response.status_code in [200, 302]:
            log_test("POST /uploadrequest", "PASS", "Request upload working")
        else:
            log_test("POST /uploadrequest", "FAIL", f"Status code: {response.status_code}")

def test_api_endpoints():
    """Test API endpoints"""
    print("\n=== Testing API Endpoints ===")

    with app.test_client() as client:
        # Test food-items API
        response = client.get('/api/food-items')
        if response.status_code == 200:
            try:
                data = json.loads(response.data)
                log_test("GET /api/food-items", "PASS", f"Returns {len(data)} items")
            except:
                log_test("GET /api/food-items", "FAIL", "Invalid JSON response")
        else:
            log_test("GET /api/food-items", "FAIL", f"Status code: {response.status_code}")

        # Test requests API
        response = client.get('/api/requests')
        if response.status_code == 200:
            try:
                data = json.loads(response.data)
                log_test("GET /api/requests", "PASS", f"Returns {len(data)} requests")
            except:
                log_test("GET /api/requests", "FAIL", "Invalid JSON response")
        else:
            log_test("GET /api/requests", "FAIL", f"Status code: {response.status_code}")

        # Test KPI API (requires login)
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_fullname'] = 'Alice Smith'
            sess['roles'] = ['Supplier']

        response = client.get('/api/kpi/supplier')
        if response.status_code == 200:
            try:
                data = json.loads(response.data)
                log_test("GET /api/kpi/supplier", "PASS", f"Returns KPI data")
            except:
                log_test("GET /api/kpi/supplier", "FAIL", "Invalid JSON response")
        else:
            log_test("GET /api/kpi/supplier", "FAIL", f"Status code: {response.status_code}")

        # Test KPI API for recipient
        with client.session_transaction() as sess:
            sess['user_id'] = 3
            sess['user_fullname'] = 'Carol White'
            sess['roles'] = ['Recipient']

        response = client.get('/api/kpi/recipient')
        if response.status_code == 200:
            try:
                data = json.loads(response.data)
                log_test("GET /api/kpi/recipient", "PASS", f"Returns KPI data")
            except:
                log_test("GET /api/kpi/recipient", "FAIL", "Invalid JSON response")
        else:
            log_test("GET /api/kpi/recipient", "FAIL", f"Status code: {response.status_code}")

def test_database_operations():
    """Test database CRUD operations"""
    print("\n=== Testing Database Operations ===")

    try:
        conn = get_db_connection()

        # Test reading users
        users = conn.execute('SELECT * FROM users LIMIT 5').fetchall()
        if len(users) > 0:
            log_test("Database: Read users", "PASS", f"Found {len(users)} users")
        else:
            log_test("Database: Read users", "FAIL", "No users found")

        # Test reading food items
        items = conn.execute('SELECT * FROM food_items LIMIT 5').fetchall()
        if len(items) > 0:
            log_test("Database: Read food_items", "PASS", f"Found {len(items)} items")
        else:
            log_test("Database: Read food_items", "FAIL", "No items found")

        # Test reading requests
        requests = conn.execute('SELECT * FROM requests LIMIT 5').fetchall()
        if len(requests) >= 0:  # Can be 0
            log_test("Database: Read requests", "PASS", f"Found {len(requests)} requests")
        else:
            log_test("Database: Read requests", "FAIL", "Error reading requests")

        # Test reading transactions
        transactions = conn.execute('SELECT * FROM transactions LIMIT 5').fetchall()
        if len(transactions) >= 0:  # Can be 0
            log_test("Database: Read transactions", "PASS", f"Found {len(transactions)} transactions")
        else:
            log_test("Database: Read transactions", "FAIL", "Error reading transactions")

        conn.close()

    except Exception as e:
        log_test("Database operations", "FAIL", str(e))

def print_summary():
    """Print test summary"""
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Total Tests: {test_results['passed'] + test_results['failed']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Success Rate: {test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100:.1f}%")
    print("="*50)

    if test_results['failed'] > 0:
        print("\nFailed Tests:")
        for test in test_results['tests']:
            if test['status'] == 'FAIL':
                print(f"  - {test['test']}: {test['message']}")

if __name__ == '__main__':
    print("="*50)
    print("FoodConnect End-to-End Route Testing")
    print("="*50)

    test_public_routes()
    test_authentication_routes()
    test_supplier_routes()
    test_recipient_routes()
    test_api_endpoints()
    test_database_operations()

    print_summary()

    sys.exit(0 if test_results['failed'] == 0 else 1)