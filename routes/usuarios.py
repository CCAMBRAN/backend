from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, get_jwt_identity
from flask_bcrypt import Bcrypt
import datetime

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

    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email y contraseña son obligatorios'}), 400
    
    cursor = get_db_connection()

    query = "SELECT password FROM usuarios WHERE email = %s"
    cursor.execute(query, (email,))

    usuario = cursor.fetchone()

    if usuario and bcrypt.check_password_hash(usuario[0], password):
        expires = datetime.timedelta(minutes=60)

        access_token = create_access_token(
            identity = str(usuario[0])
            , expires_delta=expires
            )
        cursor.close()
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'errpr': 'Credenciales inválidas'}), 401

@usuarios_bp.route('/datos', methods=['GET']) 
@jwt_required()
def datos():

    current_user = get_jwt()

    cursor = get_db_connection()

    query = "SELECT id_usuario, nombre, email FROM usuarios WHERE id_usuario = %s"
    cursor.execute(query, (current_user,))
    usuario = cursor.fetchone()

    cursor.close()

    if usuario:
        user_info = {
            'id_usuario': usuario[0],
            'nombre': usuario[1],
            'email': usuario[2]
        }
        return jsonify({'usuario': user_data}), 200
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404