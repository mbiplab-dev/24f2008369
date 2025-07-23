from flask import Flask
import os
from extensions import bcrypt

def create_app():
    app = Flask(__name__)
    app.secret_key = "lol"
    bcrypt.init_app(app)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
    app.config['DB_PATH'] = os.path.join(BASE_DIR, 'models', 'Parking.db')

    from controllers.auth_controller import auth_bp
    from controllers.user_controller import user_bp
    from controllers.admin_controller import admin_bp
    from controllers.api_controller import api_bp


    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
