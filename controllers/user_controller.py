from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
import sqlite3
from datetime import datetime


user_bp = Blueprint('user', __name__)

def get_db_path():
    return current_app.config["DB_PATH"]

@user_bp.route("/dashboard",methods=['GET', 'POST'])
def UserDashboard():     
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('SELECT full_name FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    full_name = result[0]
    search_query=''
    if request.method == 'POST':
        search_query = request.form['search'].lower()
        sort_query = request.form['sort_by']
        if (not(sort_query)):
            cursor.execute('''
                SELECT 
                    pl.id,                         
                    pl.address,                    
                    COUNT(ps.id) AS available_spots, 
                    pl.prime_location_name,        
                    pl.price_per_hour              
                FROM parking_lots pl
                LEFT JOIN parking_spots ps ON pl.id = ps.lot_id AND ps.Status = 'A'
                WHERE LOWER(pl.address) LIKE ? OR LOWER(pl.prime_location_name) LIKE ?
                GROUP BY pl.id
            ''', (f'%{search_query}%', f'%{search_query}%'))
        elif (sort_query=="low to high"):
            cursor.execute('''
                SELECT 
                    pl.id,                         
                    pl.address,                    
                    COUNT(ps.id) AS available_spots, 
                    pl.prime_location_name,        
                    pl.price_per_hour              
                FROM parking_lots pl
                LEFT JOIN parking_spots ps ON pl.id = ps.lot_id AND ps.Status = 'A'
                WHERE LOWER(pl.address) LIKE ? OR LOWER(pl.prime_location_name) LIKE ?
                GROUP BY pl.id
                ORDER BY pl.price_per_hour ASC

            ''', (f'%{search_query}%', f'%{search_query}%'))
        else :
            cursor.execute('''
                SELECT 
                    pl.id,                         
                    pl.address,                    
                    COUNT(ps.id) AS available_spots, 
                    pl.prime_location_name,        
                    pl.price_per_hour              
                FROM parking_lots pl
                LEFT JOIN parking_spots ps ON pl.id = ps.lot_id AND ps.Status = 'A'
                WHERE LOWER(pl.address) LIKE ? OR LOWER(pl.prime_location_name) LIKE ?
                GROUP BY pl.id
                ORDER BY pl.price_per_hour DESC
            ''', (f'%{search_query}%', f'%{search_query}%'))
            

    else:
        cursor.execute('''
            SELECT 
                pl.id,                   
                pl.address,                    
                COUNT(ps.id) AS available_spots, 
                pl.prime_location_name,        
                pl.price_per_hour              
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id AND ps.Status = 'A'
            GROUP BY pl.id
        ''')

    lots = cursor.fetchall()
    lots = [lot for lot in lots if lot[2] > 0]
    cursor.execute('''
        SELECT b.id, l.address, b.parking_timestamp, b.vehicle_no, b.leaving_timestamp,b.spot_id,l.price_per_hour
        FROM bookings b
        JOIN parking_lots l ON b.lot_id = l.id
        WHERE b.user_id = ?
        ORDER BY b.parking_timestamp DESC
    ''', (user_id,))
    bookings = cursor.fetchall()
    cursor.execute("SELECT username, full_name, address, pincode FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    user = {
        'username': row[0],
        'full_name': row[1],
        'address': row[2],
        'pincode': row[3]
    }

    cursor.execute("SELECT id, Status FROM parking_spots")
    spots = cursor.fetchall()
    spot_list = [{"id": row[0], "status": row[1]} for row in spots]
    
    conn.close()
    return render_template("UserTemplate.html",current="Dashboard", lots=lots, bookings=bookings , name=full_name, search_query=search_query , user=user)


@user_bp.route('/bookspot', methods=['POST'])
def BookSpot():
    spot_id = request.form['spot_id']
    lot_id = request.form['lot_id']
    user_id = request.form['user_id']
    vehicle_no = request.form['vehicle_no']
    parking_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO bookings (spot_id, lot_id, user_id,vehicle_no, parking_timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (spot_id, lot_id, user_id,vehicle_no, parking_timestamp))

    cursor.execute('''
        UPDATE parking_spots SET status = 'O' WHERE id = ?
    ''', (spot_id,))

    conn.commit()
    conn.close()

    flash("Spot booked successfully!", "success")
    return redirect(url_for('user.UserDashboard'))


@user_bp.route("/releaseparking/<int:booking_id>", methods=["POST"])
def ReleaseParking(booking_id):
    release_time = request.form.get("releasing_time")
    total_cost = request.form.get("total_cost")
    spot_id = request.form.get("spot_id")

    if not release_time or not total_cost or not spot_id:
        flash("Missing data in release form", "danger")
        return redirect(url_for("user.UserDashboard"))

    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE bookings
            SET leaving_timestamp = ?, parking_cost = ?
            WHERE id = ?
        """, (release_time, total_cost, booking_id))

        cursor.execute("""
            UPDATE parking_spots
            SET status = 'A'
            WHERE id = ?
        """, (spot_id,))

        conn.commit()
        conn.close()

        flash("Parking spot released successfully.", "success")
        return redirect(url_for("user.UserDashboard"))

    except Exception as e:
        print("Error releasing parking:", e)
        flash("An error occurred while releasing the spot.", "danger")
        return redirect(url_for("user.UserDashboard"))


@user_bp.route("/summary")
def UserSummary():
    user_id = session.get("user_id")

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('SELECT full_name FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    full_name = result[0]
    
    cursor.execute("""
        SELECT COUNT(*), SUM(parking_cost), SUM(
            JULIANDAY(leaving_timestamp) - JULIANDAY(parking_timestamp)
        ) * 24 FROM bookings WHERE user_id = ?
    """, (user_id,))
    total_bookings, total_cost, total_time = cursor.fetchone()

    if (not total_time):
        total_time=0
    
    cursor.execute("""
        SELECT parking_lots.prime_location_name, COUNT(*) as count
        FROM bookings JOIN parking_lots ON bookings.lot_id = parking_lots.id
        WHERE bookings.user_id = ?
        GROUP BY lot_id ORDER BY count DESC LIMIT 1
    """, (user_id,))
    result = cursor.fetchone()
    most_used_lot = result[0] if result else "N/A"

    avg_cost_per_hour = round(total_cost / total_time, 2) if total_time else 0
    avg_duration = round(total_time / total_bookings, 2) if total_bookings else 0

    cursor.execute("""
        SELECT parking_lots.address, COUNT(*) FROM bookings
        JOIN parking_lots ON bookings.lot_id = parking_lots.id
        WHERE bookings.user_id = ?
        GROUP BY lot_id
    """, (user_id,))
    lots_data = cursor.fetchall()
    lot_labels = [x[0] for x in lots_data]
    lot_counts = [x[1] for x in lots_data]

    cursor.execute("""
        SELECT 
            CASE 
                WHEN CAST((JULIANDAY(leaving_timestamp) - JULIANDAY(parking_timestamp)) * 24 AS INTEGER) < 1 THEN '<1 hr'
                WHEN CAST((JULIANDAY(leaving_timestamp) - JULIANDAY(parking_timestamp)) * 24 AS INTEGER) BETWEEN 1 AND 3 THEN '1-3 hrs'
                WHEN CAST((JULIANDAY(leaving_timestamp) - JULIANDAY(parking_timestamp)) * 24 AS INTEGER) > 3 THEN '>3 hr'
                ELSE 'Not Released'
            END as duration_category,
            COUNT(*) 
        FROM bookings 
        WHERE user_id = ?
        GROUP BY duration_category
    """, (user_id,))
    time_data = cursor.fetchall()
    time_labels = [x[0] for x in time_data]
    time_counts = [x[1] for x in time_data]

    cursor.execute("""
        SELECT strftime('%d', parking_timestamp) as day, SUM(parking_cost) 
        FROM bookings WHERE user_id = ?
        GROUP BY strftime('%Y-%m-%d', parking_timestamp)
        ORDER BY parking_timestamp
    """, (user_id,))
    daily_data = cursor.fetchall()
    days = [x[0] for x in daily_data]
    spend = [x[1] for x in daily_data]
    
    cursor.execute("SELECT username, full_name, address, pincode FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    user = {
        'username': row[0],
        'full_name': row[1],
        'address': row[2],
        'pincode': row[3]
    }
    
    conn.close()


    return render_template("UserTemplate.html",current = "Summary",name=full_name,
        stats={
            "total_bookings": total_bookings or 0,
            "total_cost": round(total_cost or 0, 2),
            "total_time": round(total_time or 0, 2),
            "most_used_lot": most_used_lot,
            "avg_cost_per_hour": avg_cost_per_hour,
            "avg_duration": avg_duration
        },
        charts={
            "lots": lot_labels,
            "bookings": lot_counts,
            "time_labels": time_labels,
            "time_data": time_counts,
            "days": days,
            "daily_spend": spend
        },
        user=user
    )


@user_bp.route('/editprofile', methods=['GET', 'POST'])
def EditProfile():
    user_id = session.get('user_id')
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    if request.method == 'POST':
        full_name = request.form['full_name']
        address = request.form['address']
        pincode = request.form['pincode']
        password = request.form['password']

        if password.strip():
            cursor.execute("""
                UPDATE users SET full_name = ?, address = ?, pincode = ?, password = ?
                WHERE id = ?
            """, (full_name, address, pincode, password, user_id))
        else:
            cursor.execute("""
                UPDATE users SET full_name = ?, address = ?, pincode = ?
                WHERE id = ?
            """, (full_name, address, pincode, user_id))

        conn.commit()
        conn.close()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('user.UserDashboard'))

    cursor.execute("SELECT username, full_name, address, pincode FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    user = {
        'username': row[0],
        'full_name': row[1],
        'address': row[2],
        'pincode': row[3]
    }

    return redirect(url_for("user.UserDashboard"))