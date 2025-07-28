from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, UserMixin
import sqlite3
import os
import json
from extensions import bcrypt

auth_bp = Blueprint('auth', __name__)

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def get_id(self):
        return str(self.id)


def get_db_path():
    return current_app.config["DB_PATH"]


CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'admin_credentials.json')

with open(CONFIG_PATH) as f:
    admin_credentials = json.load(f)


@auth_bp.route('/')
def LandingPage():
    return render_template("LandingPage.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if username == admin_credentials['username'] and password == admin_credentials['password']:
            session["admin"] = True
            flash("Admin login successful!", "success")
            return redirect(url_for("admin.AdminDashboard"))

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username=? ", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_id, username_db, stored_password = user
            if bcrypt.check_password_hash(stored_password, password):
                user_obj = User(user_id, username_db, stored_password)
                login_user(user_obj)
                session["user_id"] = user_id
                session["username"] = username_db
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
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "danger")

    return render_template('AuthPage.html', mode="sign-up-mode")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out , Kindly log back in !", "info")
    return redirect("/")

# Delete user account
@auth_bp.route('/delete_account')
@login_required
def DeleteAccount():
    user_id = session.get('user_id')
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    logout_user()
    session.clear()
    flash("Your account has been deleted.", "info")
    return redirect("/")
