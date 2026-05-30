from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_db, init_db
import os
import sqlite3
from datetime import datetime, timedelta
import json
import random
from decimal import Decimal
import uuid
import io
import base64

try:
    import barcode
    from barcode.writer import ImageWriter
except ImportError:
    barcode = None
    ImageWriter = None

app = Flask(__name__)
app.secret_key = 'ration-card-secret-key-2024'

# Create necessary directories
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('templates/admin', exist_ok=True)

init_db()

# Family data for each user
USER_FAMILIES = {
    'RC2024001': {  # Saravanan
        'card_holder': {'name': 'Saravanan', 'age': 48, 'relation': 'Self'},
        'members': [
            {'name': 'Uma', 'age': 43, 'relation': 'Wife', 'aadhaar': '123456789012'},
            {'name': 'Sadhana', 'age': 18, 'relation': 'Daughter', 'aadhaar': '234567890123'},
            {'name': 'Shwetha', 'age': 23, 'relation': 'Daughter', 'aadhaar': '345678901234'}
        ]
    },
    'RC2024002': {  # Cibi
        'card_holder': {'name': 'Cibi', 'age': 42, 'relation': 'Self'},
        'members': [
            {'name': 'Revathi', 'age': 42, 'relation': 'Wife', 'aadhaar': '456789012345'},
            {'name': 'Srinithi', 'age': 19, 'relation': 'Daughter', 'aadhaar': '567890123456'},
        ]
    },
    'RC2024003': {  # Easwaramurthy
        'card_holder': {'name': 'Easwaramurthy', 'age': 65, 'relation': 'Self'},
        'members': [
            {'name': 'Ganga Gowri', 'age': 43, 'relation': 'Wife', 'aadhaar': '789012345678'},
            {'name': 'Dhanavarshini', 'age': 24, 'relation': 'Daughter', 'aadhaar': '890123456789'},
            {'name': 'Vedhavarshini', 'age': 20, 'relation': 'Daughter', 'aadhaar': '901234567890'},
            {'name': 'Amirthavarshini', 'age': 19, 'relation': 'Daughter', 'aadhaar': '012345678901'}
        ]
    },
    'RC2024004': {  # Murugan
        'card_holder': {'name': 'Murugan', 'age': 52, 'relation': 'Self'},
        'members': [
            {'name': 'Kanchana', 'age': 42, 'relation': 'Wife', 'aadhaar': '112233445566'},
            {'name': 'Kavitha', 'age': 22, 'relation': 'Daughter', 'aadhaar': '223344556677'},
            {'name': 'Keerthana', 'age': 19, 'relation': 'Daughter', 'aadhaar': '334455667788'},
        ]
    },
    'ADMIN001': {  # Admin
        'card_holder': {'name': 'San', 'age': 35, 'relation': 'Self'},
        'members': [
            {'name': 'Sara', 'age': 32, 'relation': 'Wife', 'aadhaar': '556677889900'},
            {'name': 'Achu', 'age': 10, 'relation': 'Son', 'aadhaar': '667788990011'}
        ]
    }
}

# Quota based on card type
CARD_QUOTAS = {
    'AAY': {'rice': 35, 'wheat': 10, 'sugar': 3, 'kerosene': 5, 'color': 'danger', 'label': 'Antyodaya Anna Yojana'},
    'PHH': {'rice': 25, 'wheat': 8, 'sugar': 2, 'kerosene': 4, 'color': 'warning', 'label': 'Priority Household'},
    'APL': {'rice': 15, 'wheat': 6, 'sugar': 1.5, 'kerosene': 3, 'color': 'info', 'label': 'Above Poverty Line'},
    'BPL': {'rice': 20, 'wheat': 7, 'sugar': 2, 'kerosene': 4, 'color': 'secondary', 'label': 'Below Poverty Line'}
}

# Notification System
NOTIFICATIONS = {
    'RC2024001': [  # Saravanan
        {
            'id': 1,
            'title': '🎉 Festival Offer!',
            'message': 'Extra 2kg sugar for Diwali festival available this month',
            'type': 'offer',
            'date': '2024-11-10',
            'read': False,
            'important': True
        },
        {
            'id': 2,
            'title': '📅 Last Date Reminder',
            'message': 'Collect your monthly quota before 25th November',
            'type': 'reminder',
            'date': '2024-11-20',
            'read': False,
            'important': True
        },
        {
            'id': 3,
            'title': '🛒 Stock Available',
            'message': 'Fresh stock of rice and wheat available at your ration shop',
            'type': 'stock',
            'date': '2024-11-05',
            'read': True,
            'important': False
        }
    ],
    'RC2024002': [  # Cibi
        {
            'id': 1,
            'title': '🎁 Special Offer',
            'message': 'Get extra 1kg dal for this month',
            'type': 'offer',
            'date': '2024-11-12',
            'read': False,
            'important': False
        },
        {
            'id': 2,
            'title': '⏰ Last Date',
            'message': 'Collect quota before month end',
            'type': 'reminder',
            'date': '2024-11-25',
            'read': False,
            'important': True
        }
    ],
    'RC2024003': [  # Easwaramurthy
        {
            'id': 1,
            'title': '📢 Important Notice',
            'message': 'Your card verification is pending. Please visit ration office.',
            'type': 'alert',
            'date': '2024-11-08',
            'read': False,
            'important': True
        }
    ],
    'RC2024004': [  # Murugan
        {
            'id': 1,
            'title': '💰 New Scheme',
            'message': 'Extra subsidy available for BPL card holders',
            'type': 'scheme',
            'date': '2024-11-01',
            'read': False,
            'important': True
        }
    ],
    'ADMIN001': [  # Admin
        {
            'id': 1,
            'title': '📊 System Alert',
            'message': 'Low stock warning: Sugar running low in Shop No. 5',
            'type': 'alert',
            'date': '2024-11-15',
            'read': False,
            'important': True
        }
    ]
}

# ==================== HELPER FUNCTIONS ====================

def get_item_price(item_name):
    """Get price for an item"""
    prices = {
        'Rice': 3,
        'Wheat': 2,
        'Sugar': 13.5,
        'Kerosene': 25,
        'Dal': 30,
        'Oil': 45
    }
    return prices.get(item_name, 0)

# ==================== USER ROUTES ====================

@app.route('/')
def home():
    """Home page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        card_number = request.form.get('card_number')
        
        # Demo users
        demo_users = {
            'RC2024001': {'name': 'Saravanan', 'card_type': 'AAY', 'is_admin': False},
            'RC2024002': {'name': 'Cibi', 'card_type': 'PHH', 'is_admin': False},
            'RC2024003': {'name': 'Easwaramurthy', 'card_type': 'APL', 'is_admin': False},
            'RC2024004': {'name': 'Murugan', 'card_type': 'BPL', 'is_admin': False},
            'ADMIN001': {'name': 'San', 'card_type': 'AAY', 'is_admin': True}
        }
        
        if card_number in demo_users:
            user = demo_users[card_number]
            session['user_id'] = card_number
            session['card_number'] = card_number
            session['name'] = user['name']
            session['card_type'] = user['card_type']
            session['is_admin'] = user['is_admin']
            
            flash(f'Welcome {user["name"]}!', 'success')
            
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid ration card number. Try: RC2024001, RC2024002, RC2024003, RC2024004 or ADMIN001', 'danger')
    
    return render_template('login.html')

# ======== QUICK ACTION ROUTES ========

@app.route('/history')
def history():
    """View purchase history"""
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))

    card_number = session['card_number']
    db = get_db()
    cur = db.cursor()

    purchases = cur.execute("""
        SELECT id, item_name, quantity, price, purchase_date, order_id, shop_name, payment_method
        FROM purchases 
        WHERE card_number = ?
        ORDER BY purchase_date DESC
    """, (card_number,)).fetchall()

    grouped_purchases = {}
    total_spent = 0
    total_items = 0

    for purchase in purchases:
        order_id = purchase['order_id'] or f"ORDER-{purchase['id']}"
        if order_id not in grouped_purchases:
            grouped_purchases[order_id] = {
                'order_id': order_id,
                'date': purchase['purchase_date'],
                'shop': purchase['shop_name'] or 'Not specified',
                'payment_method': purchase['payment_method'] or 'cash',
                'items': [],
                'total': 0
            }

        item_total = purchase['quantity'] * purchase['price']
        grouped_purchases[order_id]['items'].append({
            'name': purchase['item_name'],
            'quantity': purchase['quantity'],
            'unit': 'kg' if purchase['item_name'] in ['Rice', 'Wheat', 'Sugar', 'Dal'] else 'L',
            'price': purchase['price'],
            'total': item_total
        })
        grouped_purchases[order_id]['total'] += item_total
        total_spent += item_total
        total_items += purchase['quantity']

    orders = list(grouped_purchases.values())
    orders.sort(key=lambda x: x['date'], reverse=True)

    monthly_stats = cur.execute("""
        SELECT 
            strftime('%Y-%m', purchase_date) as month,
            COUNT(DISTINCT COALESCE(order_id, id)) as order_count,
            SUM(quantity * price) as total_amount,
            SUM(quantity) as total_quantity
        FROM purchases 
        WHERE card_number = ?
        GROUP BY strftime('%Y-%m', purchase_date)
        ORDER BY month DESC
        LIMIT 6
    """, (card_number,)).fetchall()

    top_items = cur.execute("""
        SELECT 
            item_name,
            SUM(quantity) as total_quantity,
            SUM(quantity * price) as total_amount,
            COUNT(*) as purchase_count
        FROM purchases 
        WHERE card_number = ?
        GROUP BY item_name
        ORDER BY total_quantity DESC
        LIMIT 5
    """, (card_number,)).fetchall()

    db.close()

    total_orders = len(orders)
    avg_order_value = total_spent / total_orders if total_orders > 0 else 0

    return render_template('history.html',
                         orders=orders,
                         total_orders=total_orders,
                         total_spent=total_spent,
                         total_items=round(total_items, 2),
                         avg_order_value=avg_order_value,
                         monthly_stats=monthly_stats,
                         top_items=top_items,
                         quota_balance=1500.0)


@app.route('/history/details/<order_id>')
def history_details(order_id):
    """View details of a specific order"""
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))

    card_number = session['card_number']
    db = get_db()
    cur = db.cursor()

    order_items = cur.execute("""
        SELECT item_name, quantity, price, purchase_date, shop_name, payment_method
        FROM purchases 
        WHERE card_number = ? AND (order_id = ? OR id = ?)
        ORDER BY item_name
    """, (card_number, order_id, order_id)).fetchall()

    if not order_items:
        db.close()
        flash('Order not found', 'warning')
        return redirect(url_for('history'))

    items = []
    subtotal = 0

    for item in order_items:
        item_total = item['quantity'] * item['price']
        items.append({
            'name': item['item_name'],
            'quantity': item['quantity'],
            'unit': 'kg' if item['item_name'] in ['Rice', 'Wheat', 'Sugar', 'Dal'] else 'L',
            'price': item['price'],
            'total': item_total
        })
        subtotal += item_total

    payment_method = order_items[0]['payment_method'] or 'cash'
    delivery_charge = 50.0 if 'delivery' in payment_method.lower() else 0.0
    order_data = {
        'order_id': order_id,
        'date': order_items[0]['purchase_date'],
        'shop': order_items[0]['shop_name'] or 'Not specified',
        'payment_method': payment_method,
        'items': items,
        'subtotal': subtotal,
        'tax': subtotal * 0.05,
        'delivery_charge': delivery_charge,
        'total': subtotal * 1.05 + delivery_charge
    }

    db.close()

    return render_template('history_details.html', order=order_data)
     
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    """File complaint page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Sample ration shops
    ration_shops = [
        {'id': 1, 'shop_name': 'Fair Price Shop No. 1'},
        {'id': 2, 'shop_name': 'Fair Price Shop No. 2'},
        {'id': 3, 'shop_name': 'Fair Price Shop No. 3'}
    ]
    
    if request.method == 'POST':
        # Get complaint data
        complaint_type = request.form.get('complaint_type')
        shop_id = int(request.form.get('shop_id', 1))
        description = request.form.get('description')
        priority = request.form.get('priority', 'Medium')
        
        # Get shop name
        shop = next((s for s in ration_shops if s['id'] == shop_id), None)
        shop_name = shop['shop_name'] if shop else 'Unknown Shop'
        
        # Create complaint object
        new_complaint = {
            'id': random.randint(1000, 9999),
            'card_number': session['card_number'],
            'name': session['name'],
            'shop_id': shop_id,
            'shop_name': shop_name,
            'type': complaint_type,
            'description': description,
            'status': 'Pending',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'priority': priority
        }
        
        # Add to session
        if 'user_complaints' not in session:
            session['user_complaints'] = []
        
        session['user_complaints'].append(new_complaint)
        
        flash('Complaint submitted successfully! We will review it soon.', 'success')
        return redirect(url_for('complaint_status'))
    
    return render_template('complaint.html', ration_shops=ration_shops)

@app.route('/complaint/status')
def complaint_status():
    """View complaint status"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's complaints from session
    user_complaints = session.get('user_complaints', [])
    
    return render_template('complaint_status.html', complaints=user_complaints)

@app.route('/print/card')
def print_card():
    """Print ration card details"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    card_number = session['card_number']
    
    # Get user's family data
    family_data = USER_FAMILIES.get(card_number, {
        'card_holder': {'name': session['name'], 'age': 40, 'relation': 'Self'},
        'members': []
    })
    
    # Get quota based on card type
    quota_data = CARD_QUOTAS.get(session['card_type'], CARD_QUOTAS['APL'])
    
    print_data = {
        'user': {
            'name': session.get('name'),
            'card_number': session.get('card_number'),
            'card_type': session.get('card_type'),
            'card_label': quota_data['label'],
            'card_color': quota_data['color'],
            'issue_date': '2023-01-15',
            'expiry_date': '2028-01-15',
            'address': '123 Main Street, Chennai, Tamil Nadu - 600001',
            'phone': '+91 9876543210',
            'ration_shop': 'Fair Price Shop No. 15',
            'shop_address': 'Anna Nagar, Chennai'
        },
        'family': family_data['members'],
        'card_holder': family_data['card_holder'],
        'quota': quota_data,
        'print_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'print_id': f"PRINT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }
    
    return render_template('print_card.html', **print_data)
# ======== MAIN DASHBOARD ========

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    card_number = session['card_number']
    
    # Get user's family data
    family_data = USER_FAMILIES.get(card_number, {
        'card_holder': {'name': session['name'], 'age': 40, 'relation': 'Self'},
        'members': []
    })
    
    # Get quota based on card type
    quota_data = CARD_QUOTAS.get(session['card_type'], CARD_QUOTAS['APL'])
    
    # Get notifications for this user
    user_notifications = NOTIFICATIONS.get(card_number, [])
    
    # Count unread notifications
    unread_count = sum(1 for n in user_notifications if not n.get('read', False))
    
    # Get recent notifications (max 3)
    recent_notifications = sorted(
        user_notifications,
        key=lambda x: x['date'],
        reverse=True
    )[:3]
    
    demo_data = {
        'user': {
            'name': session.get('name'),
            'card_number': session.get('card_number'),
            'card_type': session.get('card_type'),
            'card_label': quota_data['label'],
            'card_color': quota_data['color']
        },
        'family': family_data['members'],
        'card_holder': family_data['card_holder'],
        'availability': [
            {'item_name': 'Rice', 'price': 3, 'available_quantity': 800, 'id': 1, 'unit': 'kg'},
            {'item_name': 'Wheat', 'price': 2, 'available_quantity': 600, 'id': 2, 'unit': 'kg'},
            {'item_name': 'Sugar', 'price': 13.5, 'available_quantity': 450, 'id': 3, 'unit': 'kg'},
            {'item_name': 'Kerosene', 'price': 25, 'available_quantity': 250, 'id': 4, 'unit': 'liters'},
            {'item_name': 'Dal', 'price': 30, 'available_quantity': 200, 'id': 5, 'unit': 'kg'},
            {'item_name': 'Oil', 'price': 45, 'available_quantity': 150, 'id': 6, 'unit': 'liters'}
        ],
        'quota': {
            'rice_quota': quota_data['rice'],
            'wheat_quota': quota_data['wheat'],
            'sugar_quota': quota_data['sugar'],
            'kerosene_quota': quota_data['kerosene'],
            'dal_quota': 2,
            'oil_quota': 1
        },
        'total_family_members': len(family_data['members']) + 1,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications
    }
    
    return render_template('dashboard.html', **demo_data)

# ======== OTHER USER ROUTES ========

@app.route('/profile')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    card_number = session['card_number']
    
    # Get user's family data
    family_data = USER_FAMILIES.get(card_number, {
        'card_holder': {'name': session['name'], 'age': 40, 'relation': 'Self'},
        'members': []
    })
    
    # Get quota based on card type
    quota_data = CARD_QUOTAS.get(session['card_type'], CARD_QUOTAS['APL'])
    
    profile_data = {
        'user': {
            'name': session.get('name'),
            'card_number': session.get('card_number'),
            'card_type': session.get('card_type'),
            'card_label': quota_data['label'],
            'card_color': quota_data['color'],
            'issue_date': '2023-01-15',
            'expiry_date': '2028-01-15',
            'address': '123 Main Street, Chennai, Tamil Nadu - 600001',
            'phone': '+91 9876543210',
            'ration_shop': 'Fair Price Shop No. 15',
            'shop_address': 'Anna Nagar, Chennai'
        },
        'family': family_data['members'],
        'card_holder': family_data['card_holder'],
        'total_members': len(family_data['members']) + 1
    }
    
    return render_template('profile.html', **profile_data)

@app.route('/family')
def family():
    """Family details page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    card_number = session['card_number']
    
    # Get user's family data
    family_data = USER_FAMILIES.get(card_number, {
        'card_holder': {'name': session['name'], 'age': 40, 'relation': 'Self'},
        'members': []
    })
    
    return render_template('family.html', 
                         family_data=family_data,
                         total_members=len(family_data['members']) + 1)
# ======== CONFIRM PURCHASE ROUTES ========

@app.route('/confirm-purchase', methods=['POST'])
def confirm_purchase():
    """Confirm purchase page - shows order summary before finalizing"""
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    # Get selected items from form
    selected_items = []
    total_amount = 0
    total_items = 0
    
    # Item configuration (same as in purchase.html)
    items_config = [
        {'id': 1, 'name': 'Rice', 'category': 'grain', 'price': 3.0, 'unit': 'kg'},
        {'id': 2, 'name': 'Wheat', 'category': 'grain', 'price': 2.0, 'unit': 'kg'},
        {'id': 3, 'name': 'Sugar', 'category': 'sugar', 'price': 13.5, 'unit': 'kg'},
        {'id': 4, 'name': 'Kerosene', 'category': 'fuel', 'price': 25.0, 'unit': 'L'},
        {'id': 5, 'name': 'Dal', 'category': 'pulse', 'price': 30.0, 'unit': 'kg'},
        {'id': 6, 'name': 'Oil', 'category': 'oil', 'price': 45.0, 'unit': 'L'}
    ]
    
    # Shop configuration
    shops_config = [
        {'id': 1, 'name': 'Fair Price Shop 1', 'location': 'Main Market'},
        {'id': 2, 'name': 'Fair Price Shop 2', 'location': 'New Colony'},
        {'id': 3, 'name': 'Fair Price Shop 3', 'location': 'Old City'},
        {'id': 4, 'name': 'Fair Price Shop 4', 'location': 'Industrial Area'}
    ]
    
    # Get shop details
    shop_id = request.form.get('shop_id', '1')
    shop_id = int(shop_id) if shop_id.isdigit() else 1
    selected_shop = next((shop for shop in shops_config if shop['id'] == shop_id), shops_config[0])
    
    # Get payment method
    payment_method = request.form.get('payment_method', 'quota_balance')
    
    # Collect selected items and quantities
    for item in items_config:
        quantity_key = f'quantity_{item["id"]}'
        quantity = request.form.get(quantity_key, '0')
        
        try:
            qty = float(quantity)
        except ValueError:
            qty = 0
            
        if qty > 0:
            item_total = qty * item['price']
            selected_items.append({
                'id': item['id'],
                'name': item['name'],
                'quantity': qty,
                'unit': item['unit'],
                'price_per_unit': item['price'],
                'total': round(item_total, 2)
            })
            total_amount += item_total
            total_items += qty
    
    # Validate that at least one item is selected
    if not selected_items:
        flash('Please select at least one item to purchase', 'warning')
        return redirect(url_for('purchase'))
    
    # Get user's quota balance
    user_quota_balance = 1500.0  # This would come from database in real app
    
    # Check if balance is sufficient
    if payment_method == 'quota_balance' and total_amount > user_quota_balance:
        flash(f'Insufficient quota balance! You have ₹{user_quota_balance}, but need ₹{total_amount:.2f}', 'danger')
        return redirect(url_for('purchase'))
    
    # Generate order ID
    order_id = f"ORD{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
    
    # Prepare confirmation data
    confirmation_data = {
        'order_id': order_id,
        'user': {
            'name': session.get('name'),
            'card_number': session.get('card_number'),
            'card_type': session.get('card_type')
        },
        'selected_items': selected_items,
        'selected_shop': selected_shop,
        'payment_method': payment_method,
        'payment_method_display': 'Quota Balance' if payment_method == 'quota_balance' else 'Cash',
        'subtotal': round(total_amount, 2),
        'tax': round(total_amount * 0.05, 2),  # 5% tax
        'total_amount': round(total_amount * 1.05, 2),  # subtotal + tax
        'total_items': round(total_items, 2),
        'user_quota_balance': user_quota_balance,
        'remaining_balance': round(user_quota_balance - total_amount, 2) if payment_method == 'quota_balance' else user_quota_balance,
        'transaction_date': datetime.now().strftime('%d %b %Y, %I:%M %p'),
        'delivery_option': request.form.get('delivery_option', 'pickup'),
        'special_instructions': request.form.get('special_instructions', '')
    }
    
    # Store order data in session for final confirmation
    session['pending_order'] = confirmation_data
    
    return render_template('confirm_purchase.html', **confirmation_data)


@app.route('/complete-purchase', methods=['POST'])
def complete_purchase():
    """Finalize and save the purchase"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if there's a pending order
    if 'pending_order' not in session:
        flash('No pending order found. Please start a new purchase.', 'warning')
        return redirect(url_for('purchase'))
    
    order_data = session['pending_order']
    
    # Get database connection
    db = get_db()
    cur = db.cursor()
    
    try:
        # Save each item to purchases table
        for item in order_data['selected_items']:
            cur.execute("""
                INSERT INTO purchases 
                (card_number, item_name, quantity, price, purchase_date, order_id, shop_name, payment_method)
                VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?)
            """, (
                session['card_number'],
                item['name'],
                item['quantity'],
                item['price_per_unit'],
                order_data['order_id'],
                order_data['selected_shop']['name'],
                order_data['payment_method']
            ))
        
        # Create transaction record
        cur.execute("""
            INSERT INTO transactions 
            (order_id, card_number, total_amount, payment_method, shop_name, transaction_date)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (
            order_data['order_id'],
            session['card_number'],
            order_data['total_amount'],
            order_data['payment_method'],
            order_data['selected_shop']['name']
        ))
        
        db.commit()
        
        receipt_items = []
        for item in order_data['selected_items']:
            receipt_items.append({
                'name': item['name'],
                'quantity': item['quantity'],
                'unit': item['unit'],
                'price': item['price_per_unit'],
                'total': item['total']
            })

        # Generate receipt data
        receipt_data = {
            'order_id': order_data['order_id'],
            'user_name': session['name'],
            'card_number': session['card_number'],
            'shop_name': order_data['selected_shop']['name'],
            'shop_location': order_data['selected_shop']['location'],
            'shop_address': order_data['selected_shop']['location'],
            'shop_phone': '1800-123-456',
            'items': receipt_items,
            'subtotal': order_data['subtotal'],
            'tax': order_data['tax'],
            'delivery_charge': 0.0,
            'total_amount': order_data['total_amount'],
            'payment_method': order_data['payment_method_display'],
            'payment_status': 'Paid',
            'transaction_date': datetime.now().strftime('%d %b %Y, %I:%M %p'),
            'transaction_id': f"TXN{random.randint(100000, 999999)}",
            'print_date': datetime.now().strftime('%d %b %Y, %I:%M %p'),
            'terms': 'Goods once issued through PDS cannot be returned.'
        }
        
        # Clear pending order from session
        session.pop('pending_order', None)
        
        # Save receipt data in session for receipt page
        session['last_receipt'] = receipt_data
        
        flash(f'Purchase completed successfully! Order ID: {order_data["order_id"]}', 'success')
        
        # Redirect to receipt page
        return redirect(url_for('receipt', order_id=order_data['order_id']))
        
    except Exception as e:
        db.rollback()
        flash(f'Error processing purchase: {str(e)}', 'danger')
        return redirect(url_for('purchase'))
    
    finally:
        db.close()


@app.route('/receipt/<order_id>')
def receipt(order_id):
    """Display purchase receipt"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Try to get receipt from session first
    receipt_data = session.get('last_receipt', {})
    
    # If not in session, get from database
    if not receipt_data or receipt_data.get('order_id') != order_id:
        db = get_db()
        cur = db.cursor()
        
        # Get transaction details
        transaction = cur.execute("""
            SELECT * FROM transactions 
            WHERE order_id = ? AND card_number = ?
        """, (order_id, session['card_number'])).fetchone()
        
        if not transaction:
            flash('Receipt not found', 'warning')
            return redirect(url_for('history'))
        
        # Get purchase items
        purchases = cur.execute("""
            SELECT item_name, quantity, price 
            FROM purchases 
            WHERE order_id = ?
        """, (order_id,)).fetchall()
        
        db.close()
        
        # Format receipt data
        items = []
        subtotal = 0
        for purchase in purchases:
            item_total = purchase['quantity'] * purchase['price']
            items.append({
                'name': purchase['item_name'],
                'quantity': purchase['quantity'],
                'unit': 'kg' if purchase['item_name'] in ['Rice', 'Wheat', 'Sugar', 'Dal'] else 'L',
                'price': purchase['price'],
                'total': item_total
            })
            subtotal += item_total
        
        tax = subtotal * 0.05
        total = subtotal + tax
        
        receipt_data = {
            'order_id': order_id,
            'user_name': session['name'],
            'card_number': session['card_number'],
            'shop_name': transaction['shop_name'],
            'shop_address': transaction['shop_name'],
            'shop_phone': '1800-123-456',
            'items': items,
            'subtotal': round(subtotal, 2),
            'tax': round(tax, 2),
            'delivery_charge': 0.0,
            'total_amount': round(total, 2),
            'payment_method': 'Quota Balance' if transaction['payment_method'] == 'quota_balance' else 'Cash',
            'payment_status': 'Paid',
            'transaction_date': transaction['transaction_date'],
            'transaction_id': f"TXN{random.randint(100000, 999999)}",
            'print_date': datetime.now().strftime('%d %b %Y, %I:%M %p'),
            'terms': 'Goods once issued through PDS cannot be returned.'
        }
    
    return render_template('print_receipt.html', **receipt_data)


@app.route('/cancel-purchase')
def cancel_purchase():
    """Cancel pending purchase"""
    if 'pending_order' in session:
        session.pop('pending_order', None)
        flash('Purchase cancelled', 'info')
    return redirect(url_for('purchase'))
# ======== PURCHASE ROUTES ========

@app.route("/purchase")
def purchase():
    """Purchase page with detailed interactive form"""
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    user = {
        'name': session.get('name', 'User'),
        'card_number': session.get('card_number', 'RC-2024-001'),
        'card_type': session.get('card_type', 'APL')
    }
    
    # Consistent item data
    items = [
        {'id': 1, 'name': 'Rice', 'category': 'grain', 'price': 3.0, 'stock': 500, 
         'unit': 'kg', 'user_quota': 10},
        {'id': 2, 'name': 'Wheat', 'category': 'grain', 'price': 2.0, 'stock': 300, 
         'unit': 'kg', 'user_quota': 8},
        {'id': 3, 'name': 'Sugar', 'category': 'sugar', 'price': 13.5, 'stock': 200, 
         'unit': 'kg', 'user_quota': 2},
        {'id': 4, 'name': 'Kerosene', 'category': 'fuel', 'price': 25.0, 'stock': 1000, 
         'unit': 'L', 'user_quota': 5},
        {'id': 5, 'name': 'Dal', 'category': 'pulse', 'price': 30.0, 'stock': 150, 
         'unit': 'kg', 'user_quota': 2},
        {'id': 6, 'name': 'Oil', 'category': 'oil', 'price': 45.0, 'stock': 200, 
         'unit': 'L', 'user_quota': 1}
    ]
    
    shops = [
        {'id': 1, 'name': 'Fair Price Shop 1', 'location': 'Main Market'},
        {'id': 2, 'name': 'Fair Price Shop 2', 'location': 'New Colony'},
        {'id': 3, 'name': 'Fair Price Shop 3', 'location': 'Old City'},
        {'id': 4, 'name': 'Fair Price Shop 4', 'location': 'Industrial Area'}
    ]
    
    recent_purchases = [
        {'shop': 'Fair Price Shop 1', 'date': '2024-11-15', 'amount': 450.0, 'items_count': 3},
        {'shop': 'Fair Price Shop 3', 'date': '2024-11-10', 'amount': 320.0, 'items_count': 2},
        {'shop': 'Fair Price Shop 2', 'date': '2024-11-05', 'amount': 180.0, 'items_count': 1}
    ]
    
    quota_usage = [
        {'name': 'Rice', 'used': 6.5, 'total': 10, 'unit': 'kg', 'color': 'primary'},
        {'name': 'Wheat', 'used': 3.2, 'total': 8, 'unit': 'kg', 'color': 'success'},
        {'name': 'Sugar', 'used': 0.4, 'total': 2, 'unit': 'kg', 'color': 'warning'},
        {'name': 'Kerosene', 'used': 1.5, 'total': 5, 'unit': 'L', 'color': 'info'}
    ]
    
    return render_template('purchase.html',
                         user=user,
                         items=items,
                         shops=shops,
                         recent_purchases=recent_purchases,
                         quota_usage=quota_usage,
                         quota_balance=1500.0,
                         quota_validity='31 Jan 2026',
                         quota_remaining_days=16,
                         quota_reset_date='01 Feb 2026')
@app.route("/process_purchase", methods=["POST"])
def process_purchase():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    card_number = session['card_number']
    db = get_db()
    cur = db.cursor()

    for key in request.form:
        if key.startswith('quantity_'):
            item_name = key.replace('quantity_', '')
            qty_str = request.form.get(key, '0')
            
            try:
                # Use float to handle decimal values like 3.0, 2.5, etc.
                qty = float(qty_str)
            except ValueError:
                qty = 0.0
            
            if qty > 0:
                price_str = request.form.get(f'price_{item_name}', '0')
                try:
                    price = float(price_str)
                except ValueError:
                    price = 0.0

                cur.execute("""
                    INSERT INTO purchases
                    (card_number, item_name, quantity, price, purchase_date)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (card_number, item_name, qty, price))

    db.commit()
    db.close()

    flash("Purchase saved successfully!", "success")
    return redirect(url_for('history'))

# ======== NOTIFICATION ROUTES ========

@app.route('/notifications')
def notifications():
    """Notifications page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    card_number = session['card_number']
    user_notifications = NOTIFICATIONS.get(card_number, [])
    
    # Count unread notifications
    unread_count = sum(1 for n in user_notifications if not n.get('read', False))
    
    return render_template('notifications.html',
                         notifications=user_notifications,
                         unread_count=unread_count)

@app.route('/notifications/count')
def notifications_count():
    """Get unread notifications count (for navbar badge)"""
    if 'user_id' not in session:
        return jsonify({'count': 0})
    
    card_number = session['card_number']
    user_notifications = NOTIFICATIONS.get(card_number, [])
    
    # Count unread notifications
    unread_count = sum(1 for n in user_notifications if not n.get('read', False))
    
    return jsonify({'count': unread_count})

@app.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    card_number = session['card_number']
    
    # Find and mark notification as read
    if card_number in NOTIFICATIONS:
        for notification in NOTIFICATIONS[card_number]:
            if notification['id'] == notification_id:
                notification['read'] = True
                break
    
    return jsonify({'success': True})

# ======== ADMIN ROUTES ========

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('login'))
    
    return render_template('admin/admin_dashboard.html')
@app.route('/admin/manage-stock')
def manage_stock():
    return render_template('admin/manage_stock.html')

@app.route('/admin/reports')
def view_reports():
    return render_template('admin/reports.html')

@app.route('/admin/complaints')
def handle_complaints():
    return render_template('admin/complaints.html')

@app.route('/admin/add-user')
def add_user():
    return render_template('admin/add_user.html')

# ======== LOGOUT ========

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('home'))

# ======== API ENDPOINTS ========

@app.route('/api/family/<card_number>')
def api_family(card_number):
    """API to get family details"""
    if card_number in USER_FAMILIES:
        return {
            'success': True,
            'data': USER_FAMILIES[card_number],
            'total_members': len(USER_FAMILIES[card_number]['members']) + 1
        }
    return {'success': False, 'message': 'Card not found'}

@app.route('/api/quotas')
def api_quotas():
    """API to get all quotas"""
    return {'success': True, 'data': CARD_QUOTAS}

@app.route('/api/status')
def api_status():
    return {'status': 'running', 'message': 'Ration Card System API is working'}

# ======== MAIN ========

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Ration Card System Starting...")
    print("=" * 50)
    print("\nAccess the application at:")
    print("👉 http://localhost:5000")
    print("\nDemo Login Credentials:")
    print("📱 RC2024001 - Saravanan (AAY Card Holder)")
    print("📱 RC2024002 - Cibi (PHH Card Holder)")
    print("📱 RC2024003 - Easwaramurthy (APL Card Holder)")
    print("📱 RC2024004 - Murugan (BPL Card Holder)")
    print("👑 ADMIN001 - Admin User (Full System Access)")
    print("\n" + "=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)

'''
Legacy duplicate route definitions below this point are intentionally disabled.
The active route definitions live above the __main__ block.

@app.route('/history')
def history():
    """View purchase history"""
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    card_number = session['card_number']
    db = get_db()
    cur = db.cursor()
    
    # Get all purchases for this user
    purchases = cur.execute("""
        SELECT id, item_name, quantity, price, purchase_date, order_id, shop_name, payment_method
        FROM purchases 
        WHERE card_number = ? 
        ORDER BY purchase_date DESC
    """, (card_number,)).fetchall()
    
    # Group purchases by order_id
    grouped_purchases = {}
    total_spent = 0
    total_items = 0
    
    for purchase in purchases:
        order_id = purchase['order_id'] or f"ORDER-{purchase['id']}"
        if order_id not in grouped_purchases:
            grouped_purchases[order_id] = {
                'order_id': order_id,
                'date': purchase['purchase_date'],
                'shop': purchase['shop_name'] or 'Not specified',
                'payment_method': purchase['payment_method'] or 'cash',
                'items': [],
                'total': 0
            }
        
        item_total = purchase['quantity'] * purchase['price']
        grouped_purchases[order_id]['items'].append({
            'name': purchase['item_name'],
            'quantity': purchase['quantity'],
            'unit': 'kg' if purchase['item_name'] in ['Rice', 'Wheat', 'Sugar', 'Dal'] else 'L',
            'price': purchase['price'],
            'total': item_total
        })
        grouped_purchases[order_id]['total'] += item_total
        total_spent += item_total
        total_items += purchase['quantity']
    
    # Convert to list for template
    orders = list(grouped_purchases.values())
    
    # Sort by date (newest first)
    orders.sort(key=lambda x: x['date'], reverse=True)
    
    # Get monthly statistics
    monthly_stats = cur.execute("""
        SELECT 
            strftime('%Y-%m', purchase_date) as month,
            COUNT(DISTINCT order_id) as order_count,
            SUM(quantity * price) as total_amount,
            SUM(quantity) as total_quantity
        FROM purchases 
        WHERE card_number = ?
        GROUP BY strftime('%Y-%m', purchase_date)
        ORDER BY month DESC
        LIMIT 6
    """, (card_number,)).fetchall()
    
    # Get most purchased items
    top_items = cur.execute("""
        SELECT 
            item_name,
            SUM(quantity) as total_quantity,
            SUM(quantity * price) as total_amount,
            COUNT(*) as purchase_count
        FROM purchases 
        WHERE card_number = ?
        GROUP BY item_name
        ORDER BY total_quantity DESC
        LIMIT 5
    """, (card_number,)).fetchall()
    
    db.close()
    
    # Calculate statistics
    total_orders = len(orders)
    avg_order_value = total_spent / total_orders if total_orders > 0 else 0
    
    return render_template('history.html',
                         orders=orders,
                         total_orders=total_orders,
                         total_spent=total_spent,
                         total_items=round(total_items, 2),
                         avg_order_value=avg_order_value,
                         monthly_stats=monthly_stats,
                         top_items=top_items,
                         quota_balance=1500.0)  # This would come from DB in real app


@app.route('/history/details/<order_id>')
def history_details(order_id):
    """View details of a specific order"""
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    card_number = session['card_number']
    db = get_db()
    cur = db.cursor()
    
    # Get order details
    order_items = cur.execute("""
        SELECT item_name, quantity, price, purchase_date, shop_name, payment_method
        FROM purchases 
        WHERE card_number = ? AND (order_id = ? OR id = ?)
        ORDER BY item_name
    """, (card_number, order_id, order_id)).fetchall()
    
    if not order_items:
        flash('Order not found', 'warning')
        return redirect(url_for('history'))
    
    # Calculate totals
    items = []
    subtotal = 0
    
    for item in order_items:
        item_total = item['quantity'] * item['price']
        items.append({
            'name': item['item_name'],
            'quantity': item['quantity'],
            'unit': 'kg' if item['item_name'] in ['Rice', 'Wheat', 'Sugar', 'Dal'] else 'L',
            'price': item['price'],
            'total': item_total
        })
        subtotal += item_total
    
    order_data = {
        'order_id': order_id,
        'date': order_items[0]['purchase_date'],
        'shop': order_items[0]['shop_name'] or 'Not specified',
        'payment_method': order_items[0]['payment_method'] or 'cash',
        'items': items,
        'subtotal': subtotal,
        'tax': subtotal * 0.05,  # 5% tax
        'delivery_charge': 50.0 if any('delivery' in str(item['payment_method']).lower() for item in order_items) else 0.0,
        'total': subtotal * 1.05 + (50.0 if any('delivery' in str(item['payment_method']).lower() for item in order_items) else 0.0)
    }
    
    db.close()
    
    return render_template('history_details.html', order=order_data)


@app.route('/history/delete/<int:purchase_id>', methods=['POST'])
def delete_purchase(purchase_id):
    """Delete a purchase (admin only or within time limit)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    db = get_db()
    cur = db.cursor()
    
    # Check if purchase exists and belongs to user
    purchase = cur.execute("""
        SELECT card_number FROM purchases WHERE id = ?
    """, (purchase_id,)).fetchone()
    
    if not purchase:
        db.close()
        return jsonify({'success': False, 'message': 'Purchase not found'}), 404
    
    # Check if user owns this purchase or is admin
    if purchase['card_number'] != session['card_number'] and not session.get('is_admin'):
        db.close()
        return jsonify({'success': False, 'message': 'Not authorized'}), 403
    
    # Delete the purchase
    cur.execute("DELETE FROM purchases WHERE id = ?", (purchase_id,))
    db.commit()
    db.close()
    
    flash('Purchase deleted successfully', 'success')
    return jsonify({'success': True, 'message': 'Purchase deleted'})
@app.route('/print/card')
def print_card():
    """Print ration card details"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    card_number = session['card_number']
    
    # Get user's family data
    family_data = USER_FAMILIES.get(card_number, {
        'card_holder': {'name': session['name'], 'age': 40, 'relation': 'Self'},
        'members': []
    })
    
    # Get quota based on card type
    quota_data = CARD_QUOTAS.get(session['card_type'], CARD_QUOTAS['APL'])
    
    print_data = {
        'user': {  # Keep as 'user' if template uses user
            'name': session.get('name'),
            'card_number': session.get('card_number'),
            'card_type': session.get('card_type'),
            'card_label': quota_data['label'],
            'card_color': quota_data['color'],  # Make sure this is included
            'issue_date': '2023-01-15',
            'expiry_date': '2028-01-15',
            'address': '123 Main Street, Chennai, Tamil Nadu - 600001',
            'phone': '+91 9876543210',
            'ration_shop': 'Fair Price Shop No. 15',
            'shop_address': 'Anna Nagar, Chennai'
        },
        'family': family_data['members'],
        'card_holder': family_data['card_holder'],
        'quota': quota_data,
        'print_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'print_id': f"PRINT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }
    
    return render_template('print_card.html', **print_data)
# Add these imports at the top of app.py
import barcode
from barcode.writer import ImageWriter
import io
import base64
from PIL import Image

# Add this helper function for barcode generation
def generate_barcode_base64(data, barcode_type='code128'):
    """Generate barcode and return as base64 encoded image"""
    try:
        # Create barcode
        barcode_class = barcode.get_barcode_class(barcode_type)
        barcode_image = barcode_class(data, writer=ImageWriter())
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        barcode_image.write(buffer)
        
        # Convert to base64
        buffer.seek(0)
        barcode_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return barcode_base64
    except Exception as e:
        print(f"Error generating barcode: {e}")
        # Return a simple text representation as fallback
        return None

# Update your print_card route
@app.route('/print/card')
def print_card():
    """Print ration card details with barcode"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    card_number = session['card_number']
    
    # Get user's family data
    family_data = USER_FAMILIES.get(card_number, {
        'card_holder': {'name': session['name'], 'age': 40, 'relation': 'Self'},
        'members': []
    })
    
    # Get quota based on card type
    quota_data = CARD_QUOTAS.get(session['card_type'], CARD_QUOTAS['APL'])
    
    # Generate barcode for the card number
    barcode_base64 = generate_barcode_base64(card_number)
    
    print_data = {
        'user': {
            'name': session.get('name'),
            'card_number': session.get('card_number'),
            'card_type': session.get('card_type'),
            'card_label': quota_data['label'],
            'card_color': quota_data['color'],
            'issue_date': '2023-01-15',
            'expiry_date': '2028-01-15',
            'address': '123 Main Street, Chennai, Tamil Nadu - 600001',
            'phone': '+91 9876543210',
            'ration_shop': 'Fair Price Shop No. 15',
            'shop_address': 'Anna Nagar, Chennai'
        },
        'family': family_data['members'],
        'card_holder': family_data['card_holder'],
        'quota': quota_data,
        'print_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'print_id': f"PRINT{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'barcode_data': barcode_base64,  # Add barcode data
        'barcode_text': card_number  # Text below barcode
    }
    
    return render_template('print_card.html', **print_data)
'''
