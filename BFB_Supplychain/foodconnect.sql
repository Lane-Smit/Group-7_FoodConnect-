PRAGMA foreign_keys = ON;

-- Drop existing tables
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS requests;
DROP TABLE IF EXISTS food_items;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS locations;

-- LOCATIONS
CREATE TABLE locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    province TEXT NOT NULL,
    city TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    street_address TEXT NOT NULL
);

-- USERS
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_fullname TEXT NOT NULL,
    occupation TEXT CHECK (occupation IN ('Restaurant', 'Grocery Store', 'Farm', 'Bakery', 'Manufacturer', 'Other', '')),
    location_id INTEGER NOT NULL REFERENCES locations(location_id) ON DELETE RESTRICT,
    contact_number TEXT NOT NULL CHECK (contact_number GLOB '[0-9]*' OR contact_number GLOB '+[0-9]*'),
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- USER ROLES
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('Supplier', 'Recipient')),
    PRIMARY KEY (user_id, role)
);

-- FOOD ITEMS (Surplus uploaded by Suppleirs)
CREATE TABLE food_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    food_type TEXT NOT NULL CHECK (food_type IN ('Vegetables', 'Fruits', 'Dairy', 'Bakery', 'Meat', 'Grains', 'Beverages', 'Other')),
    food_name TEXT NOT NULL,
    quantity_available NUMERIC(10,2) NOT NULL,
    expiry_date DATE NOT NULL, 
    delivery_option TEXT NOT NULL CHECK (delivery_option IN ('Pickup', 'Delivery')),
    location_id INTEGER NOT NULL REFERENCES locations(location_id) ON DELETE RESTRICT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL CHECK (status IN ('Unselected', 'Pending', 'Selected', 'Completed')) DEFAULT 'Unselected'
);

-- REQUESTS (Created by Recipeints)
CREATE TABLE requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES food_items(item_id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    quantity_needed NUMERIC(10,2) NOT NULL,
    urgency_level TEXT CHECK (urgency_level IN ('Low', 'Medium', 'High')) DEFAULT 'Medium',
    status TEXT NOT NULL CHECK (status IN ('Pending', 'Selected', 'Completed', 'Cancelled')) DEFAULT 'Pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- TRANSACTIONS 
CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL UNIQUE REFERENCES food_items(item_id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    quantity NUMERIC(10,2) NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('In-Progress', 'Completed')) DEFAULT 'In-Progress',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- TRIGGERS
CREATE TRIGGER sync_food_item_status
AFTER UPDATE OF status ON requests
FOR EACH ROW
WHEN NEW.status IN ('Selected', 'Cancelled')
BEGIN
    UPDATE food_items
    SET status = CASE
        WHEN NEW.status = 'Selected' AND food_items.status = 'Unselected' THEN 'Pending'
        WHEN NEW.status = 'Cancelled' AND food_items.status = 'Pending' THEN 'Unselected'
        ELSE food_items.status
    END
    WHERE item_id = NEW.item_id;
END;

CREATE TRIGGER validate_transaction
BEFORE INSERT ON transactions
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Invalid supplier or recipient')
    WHERE NEW.supplier_id != (SELECT user_id FROM food_items WHERE item_id = NEW.item_id)
    OR NEW.recipient_id != (SELECT recipient_id FROM requests WHERE item_id = NEW.item_id AND status = 'Selected')
    OR NOT EXISTS (SELECT 1 FROM user_roles WHERE user_id = NEW.supplier_id AND role = 'Supplier')
    OR NOT EXISTS (SELECT 1 FROM user_roles WHERE user_id = NEW.recipient_id AND role = 'Recipient');
END;

CREATE TRIGGER validate_request_quantity
BEFORE INSERT ON requests
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Quantity needed exceeds available')
    WHERE NEW.quantity_needed > (SELECT quantity_available FROM food_items WHERE item_id = NEW.item_id);
END;

CREATE TRIGGER validate_transaction_quantity
BEFORE INSERT ON transactions
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Transaction quantity exceeds available')
    WHERE NEW.quantity > (SELECT quantity_available FROM food_items WHERE item_id = NEW.item_id);
END;

-- INDEXES
CREATE INDEX idx_food_items_status ON food_items(status);
CREATE INDEX idx_food_items_user_id ON food_items(user_id);
CREATE INDEX idx_requests_item_id ON requests(item_id);
CREATE INDEX idx_requests_recipient_id ON requests(recipient_id);
CREATE INDEX idx_transactions_item_id ON transactions(item_id);
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);

-- MOCK DATA

-- LOCATIONS 
INSERT INTO locations (province, city, zip_code, street_address) VALUES
('Western Cape', 'Cape Town',        '8001', '123 Long Street'),
('Gauteng',      'Johannesburg',     '2001', '456 Main Road'),
('KwaZulu-Natal','Durban',           '4001', '789 Beachfront Avenue'),
('Gauteng',      'Pretoria',         '0083', '101 Lynnwood Road'),
('Western Cape', 'Stellenbosch',     '7600', '12 Dorp Street'),
('Free State',   'Bloemfontein',     '9301', '45 President Brand St'),
('Eastern Cape', 'Gqeberha',         '6001', '78 Marine Drive'),
('Mpumalanga',   'Mbombela',         '1200', '9 Riverside Blvd'),
('Limpopo',      'Polokwane',        '0700', '33 Market Street'),
('North West',   'Rustenburg',       '0299', '5 Platinum Road');

-- USERS
INSERT INTO users (user_fullname, occupation, location_id, contact_number, email, password, created_at) VALUES
('Alice Smith',   'Restaurant',     1, '0631234567',  'alice@example.com',  'hashed_password_1', '2025-10-27 10:00:00'),
('Bob Johnson',   'Grocery Store',  2, '+27712345678','bob@example.com',    'hashed_password_2', '2025-10-27 10:05:00'),
('Carol White',   '',               3, '0823456789',  'carol@example.com',  'hashed_password_3', '2025-10-27 10:10:00'),
('David Brown',   'Bakery',         1, '+27609876543','david@example.com',  'hashed_password_4', '2025-10-27 10:15:00'),
('Ethan Clark',   'Farm',           4, '0711111111',  'ethan@example.com',  'pass_5',            '2025-10-27 10:20:00'),
('Fatima Khan',   'Manufacturer',   5, '0722222222',  'fatima@example.com', 'pass_6',            '2025-10-27 10:25:00'),
('George Miller', 'Restaurant',     6, '0733333333',  'george@example.com', 'pass_7',            '2025-10-27 10:30:00'),
('Hannah Lee',    'Grocery Store',  7, '0744444444',  'hannah@example.com', 'pass_8',            '2025-10-27 10:35:00'),
('Ivan Petrov',   'Bakery',         8, '0755555555',  'ivan@example.com',   'pass_9',            '2025-10-27 10:40:00'),
('Julia Santos',  'Other',          9, '0766666666',  'julia@example.com',  'pass_10',           '2025-10-27 10:45:00'),
('Kevin Dlamini', 'Farm',          10, '0777777777',  'kevin@example.com',  'pass_11',           '2025-10-27 10:50:00');

-- USER ROLES
INSERT INTO user_roles (user_id, role) VALUES
(1, 'Supplier'),
(1, 'Recipient'),
(2, 'Supplier'),
(3, 'Recipient'),
(4, 'Supplier'),
(4, 'Recipient'),

-- New users: each both Supplier and Recipient
(5, 'Supplier'),   (5, 'Recipient'),
(6, 'Supplier'),   (6, 'Recipient'),
(7, 'Supplier'),   (7, 'Recipient'),
(8, 'Supplier'),   (8, 'Recipient'),
(9, 'Supplier'),   (9, 'Recipient'),
(10,'Supplier'),   (10,'Recipient'),
(11,'Supplier'),   (11,'Recipient');

-- FOOD ITEMS
INSERT INTO food_items (
    user_id, food_type, food_name, quantity_available,
    expiry_date, delivery_option, location_id, description,
    created_at, status
) VALUES
(1, 'Vegetables', 'Carrots',      10.0, '2025-12-15', 'Pickup',   1, 'Fresh carrots',                '2025-10-27 11:00:00', 'Unselected'),
(1, 'Fruits',     'Apples',        8.0, '2025-12-20', 'Delivery',  1, 'Locally grown apples',        '2025-10-27 11:05:00', 'Unselected'),
(1, 'Grains',     'Rice',         20.0, '2026-01-01', 'Pickup',    2, '2kg rice bags, sealed',       '2025-10-27 11:10:00', 'Unselected'),
(1, 'Bakery',     'Bread',         6.0, '2025-12-10', 'Delivery',  1, 'Freshly baked loaves',        '2025-10-27 11:15:00', 'Unselected'),
(1, 'Dairy',      'Milk',         15.0, '2025-12-25', 'Pickup',    3, 'Long-life milk cartons',      '2025-10-27 11:20:00', 'Unselected'),
(1, 'Meat',       'Chicken',      25.0, '2025-12-22', 'Delivery',  2, 'Frozen chicken portions',     '2025-10-27 11:25:00', 'Unselected'),
(1, 'Vegetables', 'Spinach',      12.0, '2025-12-18', 'Pickup',    4, 'Fresh spinach bundles',       '2025-10-27 11:30:00', 'Unselected'),
(1, 'Fruits',     'Bananas',      18.0, '2025-12-19', 'Pickup',    5, 'Ripe bananas',                '2025-10-27 11:35:00', 'Unselected'),
(1, 'Bakery',     'Bread Rolls',  30.0, '2026-01-05', 'Delivery',  1, 'Soft rolls in packs of 6',    '2025-10-27 11:40:00', 'Unselected'),
(1, 'Grains',     'Pasta',        40.0, '2026-02-01', 'Pickup',    2, 'Dry pasta, assorted shapes',  '2025-10-27 11:45:00', 'Unselected');

-- REQUESTS 
INSERT INTO requests (
    item_id, recipient_id, quantity_needed, urgency_level, status, created_at
) VALUES
(1,  3,  2.0, 'High',   'Pending',  '2025-10-27 12:00:00'),  -- Carol requests Carrots
(2,  4,  3.0, 'Medium', 'Pending',  '2025-10-27 12:05:00'),  -- David requests Apples
(3,  5, 10.0, 'High',   'Selected', '2025-10-27 12:10:00'),  -- Ethan requests Rice (Selected)
(4,  6,  1.0, 'Low',    'Pending',  '2025-10-27 12:15:00'),  -- Fatima requests Bread
(5,  7,  4.0, 'Medium', 'Pending',  '2025-10-27 12:20:00'),  -- George requests Milk
(6,  8,  6.0, 'High',   'Pending',  '2025-10-27 12:25:00'),  -- Hannah requests Chicken
(7,  9,  2.5, 'Medium', 'Pending',  '2025-10-27 12:30:00'),  -- Ivan requests Spinach
(8, 10,  8.0, 'High',   'Pending',  '2025-10-27 12:35:00'),  -- Julia requests Bananas
(9, 11,  5.0, 'Low',    'Pending',  '2025-10-27 12:40:00'),  -- Kevin requests Bread Rolls
(10, 3,  3.0, 'Medium', 'Pending',  '2025-10-27 12:45:00');  -- Carol requests Pasta

INSERT INTO transactions (
    item_id, supplier_id, recipient_id, quantity, status, created_at
) VALUES
(3, 1, 5, 10.0, 'Completed', '2025-10-28 09:00:00');  -- Rice from Alice to Ethan

