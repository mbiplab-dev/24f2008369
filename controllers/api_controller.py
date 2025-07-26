from flask import Blueprint, jsonify,current_app
import sqlite3
from datetime import datetime
from flask_login import login_required

api_bp = Blueprint('api', __name__)

def get_db_path():
    return current_app.config["DB_PATH"]

@api_bp.route('/api/first_free_spot/<int:lot_id>')
@login_required
def api_first_free_spot(lot_id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM parking_spots
        WHERE lot_id = ? AND Status = 'A'
        ORDER BY id ASC LIMIT 1
    ''', (lot_id,))
    row = cursor.fetchone()
    
    cursor.execute("SELECT id, Status FROM parking_spots WHERE lot_id = ?", (lot_id,))
    spots = cursor.fetchall()
    
    conn.close()
    return {'spot_id': row[0] , "spots":spots} if row else {'spot_id': None}


@api_bp.route('/api/spot-details/<int:spot_id>')
def get_spot_summary(spot_id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            ps.id AS spot_id,
            b.user_id,
            b.vehicle_no,
            b.parking_timestamp,
            pl.id AS lot_id,
            pl.prime_location_name,
            pl.address,
            pl.price_per_hour
        FROM parking_spots ps
        LEFT JOIN bookings b ON ps.id = b.spot_id AND b.leaving_timestamp IS NULL
        LEFT JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE ps.id = ?
    ''', (spot_id,))
    row=[]
    row = cursor.fetchone()
    conn.close()
    
    if row:
        parking_time = row[3]
        cost = 0
        if parking_time:
            fmt = "%Y-%m-%d %H:%M:%S"
            dt_park = datetime.strptime(parking_time, fmt)
            dt_now = datetime.now()
            hours = max((dt_now - dt_park).total_seconds() / 3600, 0.5)  # min 30 mins
            cost = round(hours * row[7], 2)

        return jsonify({
            "spot_id": row[0],
            "user_id": row[1],
            "vehicle_no": row[2],
            "parking_time": row[3],
            "estimated_cost": cost,
            "lot_id": row[4],
            "lot_name": row[5],
            "lot_address": row[6]
        })
    else:
        return jsonify({"error": "Spot not found"}), 404
