from flask import Flask
import os
from dotenv import load_dotenv
from config.db import init_db, mysql
from flask_jwt_extended import JWTManager

# Importamos las rutas de los blueprint
from routes.tareas import tareas_bp
from routes.usuarios import usuarios_bp

# Cargar las variables de entorno
load_dotenv()


def create_app():  # <-Funcion para crear la app

    # Instancia de la app
    app = Flask(__name__)

    # Configurar la base de datos
    init_db(app)

    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET')
    jwt = JWTManager(app)

    #Registrar el blueprint
    app.register_blueprint(tareas_bp, url_prefix='/tareas')
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')

    return app


# Crear la app
app = create_app()

if __name__ == "__main__":

    #Obtenemos el puerto
    port = int(os.getenv("PORT",8080))

    #Corremos la app
    app.run(host="0.0.0.0", port=port, debug=True)