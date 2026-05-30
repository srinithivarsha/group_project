import sqlite3

DB_NAME = "ration.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    cur = db.cursor()

    # ================= USERS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_number TEXT UNIQUE,
        name TEXT,
        card_type TEXT,
        is_admin INTEGER DEFAULT 0
    )
    """)

    # ================= ITEMS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL
    )
    """)

    # ================= PURCHASES TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_number TEXT,
        item_name TEXT,
        quantity REAL,
        price REAL,
        purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        order_id TEXT,
        shop_name TEXT,
        payment_method TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE,
        card_number TEXT,
        total_amount REAL,
        payment_method TEXT,
        shop_name TEXT,
        transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("PRAGMA table_info(purchases)")
    existing_columns = {row[1] for row in cur.fetchall()}
    for column_name, column_type in {
        "order_id": "TEXT",
        "shop_name": "TEXT",
        "payment_method": "TEXT",
    }.items():
        if column_name not in existing_columns:
            cur.execute(f"ALTER TABLE purchases ADD COLUMN {column_name} {column_type}")

    # ================= INSERT DEFAULT ITEMS (ONLY ONCE) =================
    cur.execute("SELECT COUNT(*) FROM items")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO items (name, price) VALUES (?, ?)",
            [
                ("Rice", 3),
                ("Wheat", 2),
                ("Sugar", 13.5),
                ("Kerosene", 25),
                ("Dal", 30),
                ("Oil", 45)
            ]
        )

    db.commit()
    db.close()
