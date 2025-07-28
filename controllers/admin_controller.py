from flask import Blueprint, render_template, request, redirect, url_for, flash,current_app,session
from flask_login import logout_user
import sqlite3
from werkzeug.utils import secure_filename
import os

admin_bp = Blueprint('admin', __name__)

def get_db_path():
    return current_app.config["DB_PATH"]

def get_upload_path():
    return current_app.config["UPLOAD_FOLDER"]


@admin_bp.route("/admindashboard")
def AdminDashboard():
    if not session.get("admin"):
        logout_user() 
        session.clear()
        flash("Admin login required!", "danger")
        return redirect(url_for("auth.login"))    
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM parking_lots")
    lots = cursor.fetchall()

    all_lots = []

    for lot in lots:
        lot_id = lot["id"]
        cursor.execute("SELECT * FROM parking_spots WHERE lot_id = ?", (lot_id,))
        spots = cursor.fetchall()

        available_spots = sum(1 for spot in spots if spot["Status"] == "A")
        all_lots.append({
            "id": lot["id"],
            "prime_location_name": lot["prime_location_name"],
            "address": lot["address"],
            "pincode":lot["pincode"],
            "price_per_hour":lot["price_per_hour"],
            "max_spots": lot["max_spots"],
            "map_link" : lot["map_link"],
            "available_spots": available_spots,
            "spots": [
                {
                    "spot_id":spot['id'],
                    "label": f"S{spot['id']}",
                    "is_available": spot["Status"]
                } for spot in spots
            ]
        })

    conn.close()
    return render_template("AdminTemplate.html",current="Dashboard", lots=all_lots)


@admin_bp.route('/users')
def show_users():
    if not session.get("admin"):
        logout_user() 
        session.clear()
        flash("Admin login required!", "danger")
        return redirect(url_for("auth.login")) 
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return render_template("AdminTemplate.html",current="Users", users=users)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@admin_bp.route('/addparkinglot', methods=['POST'])
def AddParkingLot():
    if not session.get("admin"):
        logout_user() 
        session.clear()
        flash("Admin login required!", "danger")
        return redirect(url_for("auth.login")) 
    name = request.form['name']
    address = request.form['address']
    map_link = request.form['map_link']
    pincode = request.form['pincode']
    price = float(request.form['price_per_hour'])
    max_spots = int(request.form['max_spots'])

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO parking_lots (prime_location_name, price_per_hour, address, pincode, max_spots, map_link)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, price, address, pincode, max_spots,map_link))

    lot_id = cursor.lastrowid 

    for i in range(1, max_spots + 1):
        cursor.execute('''
            INSERT INTO parking_spots (lot_id, Status)
            VALUES (?, ?)
        ''', (lot_id, 'A'))

    conn.commit()
    conn.close()
    
    image = request.files.get('image')
    if image and allowed_file(image.filename):
        filename = secure_filename(f"lot_{lot_id}" + ".png")
        image_path = os.path.join(get_upload_path(), filename)
        image.save(image_path)
    return redirect(url_for("admin.AdminDashboard"))


@admin_bp.route('/editparkinglot/<int:lot_id>', methods=['POST'])
def EditParkingLot(lot_id):
    if not session.get("admin"):
        logout_user() 
        session.clear()
        flash("Admin login required!", "danger")
        return redirect(url_for("auth.login")) 
    name = request.form['name']
    address = request.form['address']
    pincode = request.form['pincode']
    price = float(request.form['price_per_hour'])
    max_spots = int(request.form['max_spots'])
    map_link = request.form['map_link']
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute('SELECT max_spots FROM parking_lots WHERE id = ?', (lot_id,))
    result = cursor.fetchone()

    if result:
        current_max_spots = result[0]

        cursor.execute('''
            UPDATE parking_lots
            SET prime_location_name = ?, price_per_hour = ?, address = ?, pincode = ?, max_spots = ?, map_link = ?
            WHERE id = ?
        ''', (name, price, address, pincode, max_spots, map_link, lot_id))

        if max_spots > current_max_spots:
            for _ in range(current_max_spots + 1, max_spots + 1):
                cursor.execute('''
                    INSERT INTO parking_spots (lot_id, Status)
                    VALUES (?, ?)
                ''', (lot_id, 'A'))

        elif max_spots < current_max_spots:
            spots_to_remove = current_max_spots - max_spots
            cursor.execute('''
                SELECT id FROM parking_spots
                WHERE lot_id = ? AND Status = 'A'
                ORDER BY id DESC
                LIMIT ?
            ''', (lot_id, spots_to_remove))

            available_spots = cursor.fetchall()

            if len(available_spots) < spots_to_remove:
                conn.close()
                flash("Cannot reduce max spots. Some of the last spots are currently occupied.", "danger")
                return redirect(url_for("admin.AdminDashboard"))

            for spot in available_spots:
                cursor.execute('DELETE FROM parking_spots WHERE id = ?', (spot[0],))

        conn.commit()
        conn.close()
        
        image = request.files.get('editImage')
        if image and allowed_file(image.filename):
            filename = secure_filename(f"lot_{lot_id}" + ".png")
            image_path = os.path.join(get_upload_path(), filename)
            image.save(image_path)
        

        flash("Parking lot updated successfully!", "success")
    else:
        conn.close()
        flash("Parking lot not found.", "danger")

    return redirect(url_for("admin.AdminDashboard"))


@admin_bp.route('/deleteparkinglot/<int:lot_id>', methods=['POST'])
def DeleteParkingLot(lot_id):
    if not session.get("admin"):
        logout_user() 
        session.clear()
        flash("Admin login required!", "danger")
        return redirect(url_for("auth.login")) 
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM parking_spots
        WHERE lot_id = ? AND Status != 'A'
    ''', (lot_id,))
    occupied_count = cursor.fetchone()[0]

    if occupied_count > 0:
        conn.close()
        flash("Cannot delete the parking lot. Some spots are currently occupied.", "danger")
        return redirect(url_for("admin.AdminDashboard"))
    
    cursor.execute('DELETE FROM parking_spots WHERE lot_id = ?', (lot_id,))
    cursor.execute('DELETE FROM parking_lots WHERE id = ?', (lot_id,))

    conn.commit()
    conn.close()

    flash("Parking lot deleted successfully.", "success")
    return redirect(url_for("admin.AdminDashboard"))

@admin_bp.route('/deletespot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    if not session.get("admin"):
        logout_user() 
        session.clear()
        flash("Admin login required!", "danger")
        return redirect(url_for("auth.login")) 
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("SELECT Status, lot_id FROM parking_spots WHERE id = ?", (spot_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        flash("Parking spot not found.", "danger")
        return redirect(request.referrer)

    status, lot_id = row
    if status != 'A':
        conn.close()
        flash("Cannot delete an occupied spot.", "warning")
        return redirect(request.referrer)

    cursor.execute("DELETE FROM parking_spots WHERE id = ?", (spot_id,))

    cursor.execute("UPDATE parking_lots SET max_spots = max_spots - 1 WHERE id = ?", (lot_id,))

    conn.commit()
    conn.close()

    flash("Parking spot deleted successfully.", "success")
    return redirect(url_for('admin.AdminDashboard'))


@admin_bp.route('/search', methods=['GET', 'POST'])
def AdminSearch():
    if not session.get("admin"):
        logout_user() 
        session.clear()
        flash("Admin login required!", "danger")
        return redirect(url_for("auth.login")) 
    if request.method == 'POST':
        filter_by = request.form['filter_by']
        query = request.form['query']
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        results = []

        if filter_by == 'Lot Address':
            cursor.execute("SELECT * FROM parking_lots WHERE address LIKE ?", (f"%{query}%",))
            lots = cursor.fetchall()

            for lot in lots:
                lot_id = lot["id"]
                cursor.execute("SELECT * FROM parking_spots WHERE lot_id = ?", (lot_id,))
                spots = cursor.fetchall()

                available_spots = sum(1 for spot in spots if spot["Status"] == "A")
                results.append({
                "id": lot["id"],
                "prime_location_name": lot["prime_location_name"],
                "address": lot["address"],
                "pincode":lot["pincode"],
                "price_per_hour":lot["price_per_hour"],
                "max_spots": lot["max_spots"],
                "available_spots": available_spots,
                "spots": [
                    {
                        "spot_id":spot['id'],
                        "label": f"S{spot['id']}",
                        "is_available": spot["Status"]
                    } for spot in spots
                ]
            })
            return render_template("AdminTemplate.html",current="Search", lots=results,filter_by=filter_by, search_query=query)

        if filter_by == 'Lot Id':
            cursor.execute("SELECT * FROM parking_lots WHERE id = ?", (query,))
            lots = cursor.fetchall()

            for lot in lots:
                lot_id = lot["id"]
                cursor.execute("SELECT * FROM parking_spots WHERE lot_id = ?", (lot_id,))
                spots = cursor.fetchall()

                available_spots = sum(1 for spot in spots if spot["Status"] == "A")
                results.append({
                "id": lot["id"],
                "prime_location_name": lot["prime_location_name"],
                "address": lot["address"],
                "pincode":lot["pincode"],
                "price_per_hour":lot["price_per_hour"],
                "max_spots": lot["max_spots"],
                "available_spots": available_spots,
                "spots": [
                    {
                        "spot_id":spot['id'],
                        "label": f"S{spot['id']}",
                        "is_available": spot["Status"]
                    } for spot in spots
                ]
            })
            return render_template("AdminTemplate.html",current="Search", lots=results,filter_by=filter_by, search_query=query)

        elif filter_by == 'User Id':
            cursor.execute('SELECT * FROM users WHERE id=?',(query))
            users = cursor.fetchall()
            return render_template("AdminTemplate.html",current="Search", users=users,filter_by=filter_by, search_query=query)
        elif filter_by == 'User Address':
            cursor.execute('SELECT * FROM users WHERE address LIKE ?', (f"%{query}%",))
            users = cursor.fetchall()
            return render_template("AdminTemplate.html",current="Search", users=users,filter_by=filter_by, search_query=query)
        elif filter_by == 'Spot Id':
           cursor.execute('''
                SELECT pl.*,ps.Status
                FROM parking_spots ps
                JOIN parking_lots pl ON ps.lot_id = pl.id
                WHERE ps.id = ?
            ''', (query,))
           results = cursor.fetchone()
           return render_template("AdminTemplate.html",current="Search", results=results,filter_by=filter_by, search_query=query)

        else:
            pass
        conn.close()

        return render_template("AdminTemplate.html",current="Search")

    return render_template("AdminTemplate.html",current="Search")



@admin_bp.route('/adminsummary')
def AdminSummary():
    if not session.get("admin"):
        logout_user() 
        session.clear()
        flash("Admin login required!", "danger")
        return redirect(url_for("auth.login")) 
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(parking_cost) FROM bookings WHERE leaving_timestamp IS NOT NULL")
    total_income = cursor.fetchone()[0] or 0

    cursor.execute('''
        SELECT pl.prime_location_name, COUNT(b.id) as bookings
        FROM bookings b
        JOIN parking_spots ps ON b.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        GROUP BY ps.lot_id
        ORDER BY bookings DESC
        LIMIT 1
    ''')
    result = cursor.fetchone()
    most_used_lot = result[0] if result else "N/A"

    cursor.execute('''
        SELECT pl.prime_location_name, SUM(b.parking_cost) as income
        FROM bookings b
        JOIN parking_spots ps ON b.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE b.leaving_timestamp IS NOT NULL
        GROUP BY ps.lot_id
    ''')
    rows = cursor.fetchall()
    lot_names = [row[0] for row in rows]
    lot_income = [round(row[1], 2) for row in rows]

    cursor.execute('''
        SELECT DATE(parking_timestamp) as date, SUM(parking_cost)
        FROM bookings
        WHERE leaving_timestamp IS NOT NULL
        GROUP BY DATE(parking_timestamp)
        ORDER BY date DESC
        LIMIT 7
    ''')
    daily_rows = cursor.fetchall()
    days = [row[0] for row in daily_rows][::-1]
    daily_income = [round(row[1], 2) for row in daily_rows][::-1]

    cursor.execute('''
    SELECT DATE(parking_timestamp) as date, COUNT(*) as bookings
    FROM bookings
    GROUP BY DATE(parking_timestamp)
    ORDER BY date DESC
    LIMIT 7
    ''')
    booking_rows = cursor.fetchall()
    booking_days = [row[0] for row in booking_rows][::-1]
    daily_bookings = [row[1] for row in booking_rows][::-1]

    conn.close()

    return render_template("AdminTemplate.html",current="Summary", 
        stats={
            'total_users': total_users,
            'total_bookings': total_bookings,
            'total_income': round(total_income, 2),
            'most_used_lot': most_used_lot
        },
        charts={
            'lot_names': lot_names,
            'lot_income': lot_income,
            'days': days,
            'daily_income': daily_income
        },
        booking_chart={
            'booking_days': booking_days,
            'daily_bookings': daily_bookings
        }

    )
  
