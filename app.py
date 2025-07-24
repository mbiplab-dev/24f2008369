from flask import Flask
import os
import sqlite3
from extensions import bcrypt, login_manager
from controllers.user_controller import User  

app = Flask(__name__)
app.secret_key = "lol" 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['DB_PATH'] = os.path.join(BASE_DIR, 'models', 'Parking.db')

bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(app.config["DB_PATH"])
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2])
    return None

from controllers.auth_controller import auth_bp
from controllers.user_controller import user_bp
from controllers.admin_controller import admin_bp
from controllers.api_controller import api_bp
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)


if __name__ == '__main__':
    app.run(debug=True)
