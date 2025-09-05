from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt
from flask_bcrypt import Bcrypt

from config.db import get_db_connection

import os 
from dotenv import load_dotenv

#cargsgo variables de entorno
load_dotenv()   

usuarios_bp = Blueprint('usuarios', __name__)
bcrypt = Bcrypt()

@usuarios_bp.route('registrar', methods=['POST'])
def registrar():
    data = request.get_json()

    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')

    # Validar que los campos no estén vacíos
    if not nombre or not email or not password:
        return jsonify({'message': 'Todos los campos son obligatorios'}), 400
    
    cursor = get_db_connection()

    try:
        #verificar si el usuario no existe
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({'message': 'El usuario ya existe'}), 400
        
        # Hashear la contraseña
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insertar el nuevo usuario en la base de datos
        cursor.execute("INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)", (nombre , email, hashed_password))

        # Guardar los cambios
        cursor.connection.commit()

        return jsonify({'message': 'Usuario registrado exitosamente'}), 201


    except Exception as e:
        return jsonify({'message': f'Error al registrar el usuario: {str(e)}'}), 500

    finally:
        cursor.close()

@usuarios_bp.route('login', methods=['POST'])
def login():

    data = request.json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email y contraseña son obligatorios'}), 400
    
    cursor = get_db_connection()
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))