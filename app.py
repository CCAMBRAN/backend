from flask import Flask
import os
from dotenv import load_dotenv
from config.db import init_db, mysql
from flask_jwt_extended import JWTManager

from routes.tareas import tareas_bp
from routes.usuarios import usuarios_bp

load_dotenv()

def create_app():
    app = Flask(__name__)

    init_db(app)
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET')
    jwt = JWTManager(app)

    app.register_blueprint(tareas_bp, url_prefix='/tareas')
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    return app

app=create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    app.run(host='0.0.0.0', port=port, debug=True)