from flask import Flask, render_template, request, url_for, redirect, send_file, session , flash , jsonify
import sqlite3
from jinja2 import Template
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR,'static', 'uploads')
DB_PATH = os.path.join(BASE_DIR, "models", "Parking.db")

if not os.path.exists(DB_PATH):
    print("Database not initialized. Please run 'model.py' first before starting the Application")
    exit()

app = Flask(__name__)
app.secret_key = "lol"

bcrypt = Bcrypt(app)


@app.route('/')
def LandingPage():
    return render_template("LandingPage.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if username=="admin" and password=="admin":
            return redirect(url_for("AdminDashboard"))
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, password FROM users WHERE username=? ", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_id, username, stored_password = user
            if (bcrypt.check_password_hash(stored_password, password)):
                session["user_id"] = user_id
                session["username"] = username
                flash("Login successful!", "success")
                return redirect(url_for("UserDashboard")) 
            else:
                flash("Incorrect password", "danger")
        else:
            flash("User not found", "danger")

    return render_template("AuthPage.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        password = request.form['password']
        address = request.form.get('address', '')
        pincode = request.form.get('pincode', '')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO users (username, full_name, password, address, pincode)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, full_name, hashed_password, address, pincode))

            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username or email already exists!"
    return render_template('AuthPage.html',mode="sign-up-mode")



@app.route("/dashboard",methods=['GET', 'POST'])
def UserDashboard():     
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("Login"))

    conn = sqlite3.connect(DB_PATH)
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



@app.route("/admindashboard")
def AdminDashboard():
    conn = sqlite3.connect(DB_PATH)
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


@app.route('/users')
def show_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows dict-like access
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return render_template("AdminTemplate.html",current="Users", users=users)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/addparkinglot', methods=['POST'])
def AddParkingLot():
    name = request.form['name']
    address = request.form['address']
    pincode = request.form['pincode']
    price = float(request.form['price_per_hour'])
    max_spots = int(request.form['max_spots'])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO parking_lots (prime_location_name, price_per_hour, address, pincode, max_spots)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, price, address, pincode, max_spots))

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
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(image_path)
    return redirect(url_for("AdminDashboard"))


@app.route('/editparkinglot/<int:lot_id>', methods=['POST'])
def EditParkingLot(lot_id):
    name = request.form['name']
    address = request.form['address']
    pincode = request.form['pincode']
    price = float(request.form['price_per_hour'])
    max_spots = int(request.form['max_spots'])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT max_spots FROM parking_lots WHERE id = ?', (lot_id,))
    result = cursor.fetchone()

    if result:
        current_max_spots = result[0]

        cursor.execute('''
            UPDATE parking_lots
            SET prime_location_name = ?, price_per_hour = ?, address = ?, pincode = ?, max_spots = ?
            WHERE id = ?
        ''', (name, price, address, pincode, max_spots, lot_id))

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
                return redirect(url_for("AdminDashboard"))

            for spot in available_spots:
                cursor.execute('DELETE FROM parking_spots WHERE id = ?', (spot[0],))

        conn.commit()
        conn.close()
        
        image = request.files.get('editImage')
        if image and allowed_file(image.filename):
            filename = secure_filename(f"lot_{lot_id}" + ".png")
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(image_path)
        

        flash("Parking lot updated successfully!", "success")
    else:
        conn.close()
        flash("Parking lot not found.", "danger")

    return redirect(url_for("AdminDashboard"))


@app.route('/deleteparkinglot/<int:lot_id>', methods=['POST'])
def DeleteParkingLot(lot_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM parking_spots
        WHERE lot_id = ? AND Status != 'A'
    ''', (lot_id,))
    occupied_count = cursor.fetchone()[0]

    if occupied_count > 0:
        conn.close()
        flash("Cannot delete the parking lot. Some spots are currently occupied.", "danger")
        return redirect(url_for("AdminDashboard"))
    
    cursor.execute('DELETE FROM parking_spots WHERE lot_id = ?', (lot_id,))
    cursor.execute('DELETE FROM parking_lots WHERE id = ?', (lot_id,))

    conn.commit()
    conn.close()

    flash("Parking lot deleted successfully.", "success")
    return redirect(url_for("AdminDashboard"))



@app.route('/bookspot', methods=['POST'])
def BookSpot():
    spot_id = request.form['spot_id']
    lot_id = request.form['lot_id']
    user_id = request.form['user_id']
    vehicle_no = request.form['vehicle_no']
    parking_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
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
    return redirect(url_for('UserDashboard'))


@app.route('/api/first_free_spot/<int:lot_id>')
def api_first_free_spot(lot_id):
    conn = sqlite3.connect(DB_PATH)
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


@app.route("/releaseparking/<int:booking_id>", methods=["POST"])
def ReleaseParking(booking_id):
    release_time = request.form.get("releasing_time")
    total_cost = request.form.get("total_cost")
    spot_id = request.form.get("spot_id")

    if not release_time or not total_cost or not spot_id:
        flash("Missing data in release form", "danger")
        return redirect(url_for("UserDashboard"))

    try:
        conn = sqlite3.connect(DB_PATH)
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
        return redirect(url_for("UserDashboard"))

    except Exception as e:
        print("Error releasing parking:", e)
        flash("An error occurred while releasing the spot.", "danger")
        return redirect(url_for("UserDashboard"))


@app.route("/summary")
def UserSummary():
    user_id = session.get("user_id")

    conn = sqlite3.connect(DB_PATH)
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


@app.route('/deletespot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    conn = sqlite3.connect(DB_PATH)
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
    return redirect(url_for('AdminDashboard'))


@app.route('/search', methods=['GET', 'POST'])
def AdminSearch():
    if request.method == 'POST':
        filter_by = request.form['filter_by']
        query = request.form['query']
        conn = sqlite3.connect(DB_PATH)
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



@app.route('/adminsummary')
def AdminSummary():
    conn = sqlite3.connect(DB_PATH)
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

    # All users
    cursor.execute("SELECT id, username, full_name, address, pincode FROM users")
    users = [dict(zip(['id', 'username', 'full_name', 'address', 'pincode'], row)) for row in cursor.fetchall()]

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
        users=users
    )
  

@app.route('/api/spot-details/<int:spot_id>')
def get_spot_summary(spot_id):
    conn = sqlite3.connect(DB_PATH)
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

  
@app.route('/editprofile', methods=['GET', 'POST'])
def EditProfile():
    user_id = session.get('user_id')
    conn = sqlite3.connect(DB_PATH)
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
        return redirect(url_for('UserDashboard'))

    cursor.execute("SELECT username, full_name, address, pincode FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    user = {
        'username': row[0],
        'full_name': row[1],
        'address': row[2],
        'pincode': row[3]
    }

    return redirect(url_for("UserDashboard"))
  
    

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/") 


@app.route('/delete_account')
def DeleteAccount():
    user_id = session.get('user_id')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    session.clear()
    flash("Your account has been deleted.", "info")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug = True)