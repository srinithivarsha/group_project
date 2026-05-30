import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect('ration_card.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            card_type TEXT CHECK(card_type IN ('PHH', 'AAY', 'NPHH', 'SPHH')),
            issue_date DATE,
            expiry_date DATE,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Family members table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS family_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            relation TEXT,
            aadhaar_number TEXT UNIQUE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Monthly quota table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_quota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_type TEXT UNIQUE NOT NULL,
            rice_quota REAL DEFAULT 0,
            wheat_quota REAL DEFAULT 0,
            sugar_quota REAL DEFAULT 0,
            kerosene_quota REAL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Stock availability table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            price REAL NOT NULL,
            total_quantity REAL NOT NULL,
            available_quantity REAL NOT NULL,
            date DATE NOT NULL,
            UNIQUE(item_name, date)
        )
    ''')
    
    # Purchase history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Ration shops table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ration_shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_number TEXT UNIQUE NOT NULL,
            shop_name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT,
            opening_time TIME,
            closing_time TIME,
            incharge_name TEXT
        )
    ''')
    
    # Complaints table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            shop_id INTEGER NOT NULL,
            complaint_type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            resolution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (shop_id) REFERENCES ration_shops (id)
        )
    ''')
    
    # Special offers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS special_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            card_type TEXT,
            start_date DATE,
            end_date DATE,
            extra_quota REAL DEFAULT 0,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_sample_data():
    conn = sqlite3.connect('ration_card.db')
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Add sample users
    cursor.execute('''
        INSERT INTO users (card_number, name, phone, card_type, is_admin)
        VALUES 
        ('RC2024001', 'Rahul Sharma', '9876543210', 'AAY', 0),
        ('RC2024002', 'Priya Patel', '9876543211', 'PHH', 0),
        ('RC2024003', 'Amit Kumar', '9876543212', 'NPHH', 0),
        ('ADMIN001', 'Admin User', '9999999999', 'AAY', 1)
    ''')
    
    # Add family members
    cursor.execute('''
        INSERT INTO family_members (user_id, name, age, relation)
        VALUES 
        (1, 'Sunita Sharma', 45, 'Wife'),
        (1, 'Rohit Sharma', 18, 'Son'),
        (2, 'Ramesh Patel', 50, 'Husband'),
        (2, 'Neha Patel', 20, 'Daughter')
    ''')
    
    # Add monthly quotas
    cursor.execute('''
        INSERT OR REPLACE INTO monthly_quota (card_type, rice_quota, wheat_quota, sugar_quota, kerosene_quota)
        VALUES 
        ('AAY', 35, 10, 3, 5),
        ('PHH', 25, 8, 2, 4),
        ('NPHH', 20, 6, 1.5, 3),
        ('SPHH', 15, 5, 1, 2)
    ''')
    
    # Add today's stock
    today = datetime.now().date()
    cursor.execute('''
        INSERT OR REPLACE INTO stock_availability (item_name, price, total_quantity, available_quantity, date)
        VALUES 
        ('Rice', 3, 1000, 800, ?),
        ('Wheat', 2, 800, 600, ?),
        ('Sugar', 13.5, 500, 450, ?),
        ('Kerosene', 25, 300, 250, ?)
    ''', (today, today, today, today))
    
    # Add ration shops
    cursor.execute('''
        INSERT OR REPLACE INTO ration_shops (shop_number, shop_name, address, phone, opening_time, closing_time)
        VALUES 
        ('RS001', 'Fair Price Shop No. 1', 'Main Market, Delhi', '011-23456789', '09:00', '18:00'),
        ('RS002', 'Fair Price Shop No. 2', 'Sector 15, Noida', '0120-2345678', '08:00', '17:00')
    ''')
    
    # Add sample purchases
    for i in range(1, 4):
        cursor.execute('''
            INSERT INTO purchase_history (user_id, item_name, quantity, price, purchase_date)
            VALUES (?, 'Rice', 5, 3, ?)
        ''', (i, (datetime.now() - timedelta(days=i)).date()))
    
    # Add special offers
    cursor.execute('''
        INSERT OR REPLACE INTO special_offers (title, description, card_type, start_date, end_date, extra_quota)
        VALUES 
        ('Diwali Special', 'Extra 2kg sugar for festival', 'AAY', '2024-10-20', '2024-11-10', 2),
        ('Republic Day Offer', 'Additional 1kg rice for all card holders', NULL, '2024-01-20', '2024-01-30', 1)
    ''')
    
    conn.commit()
    conn.close()