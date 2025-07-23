from flask import Blueprint, render_template, request, redirect, url_for, flash, session,current_app
import sqlite3
from extensions import bcrypt

auth_bp = Blueprint('auth', __name__)

def get_db_path():
    return current_app.config["DB_PATH"]

@auth_bp.route('/')
def LandingPage():
    return render_template("LandingPage.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if username=="admin" and password=="admin":
            return redirect(url_for("admin.AdminDashboard"))
        conn = sqlite3.connect(get_db_path())
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
                return redirect(url_for("user.UserDashboard")) 
            else:
                flash("Incorrect password", "danger")
        else:
            flash("User not found", "danger")

    return render_template("AuthPage.html")


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        password = request.form['password']
        address = request.form.get('address', '')
        pincode = request.form.get('pincode', '')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        try:
            conn = sqlite3.connect(get_db_path())
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


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/") 


@auth_bp.route('/delete_account')
def DeleteAccount():
    user_id = session.get('user_id')
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    session.clear()
    flash("Your account has been deleted.", "info")
    return redirect("/")
