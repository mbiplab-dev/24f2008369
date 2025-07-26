import sqlite3
import os

models_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(models_dir, exist_ok=True)

db_path = os.path.join(models_dir, "Parking.db")

connect = sqlite3.connect(db_path)
cursor = connect.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    password TEXT NOT NULL,
    address TEXT,
    pincode TEXT
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS parking_lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prime_location_name TEXT NOT NULL,
    price_per_hour REAL NOT NULL,
    address TEXT NOT NULL,
    pincode TEXT NOT NULL,
    max_spots INTEGER NOT NULL,
    map_link TEXT NOT NULL
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS parking_spots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id INTEGER NOT NULL,
    status TEXT DEFAULT 'A',
    FOREIGN KEY (lot_id) REFERENCES parking_lots(id)
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spot_id INTEGER NOT NULL,
    lot_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    vehicle_no TEXT NOT NULL,
    parking_timestamp TEXT NOT NULL,
    leaving_timestamp TEXT,
    parking_cost REAL,
    FOREIGN KEY (spot_id) REFERENCES parking_spots(id),
    FOREIGN KEY (lot_id) REFERENCES parking_lots(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

connect.commit()
connect.close()

print(f"Database created at: {db_path}")