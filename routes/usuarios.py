from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, get_jwt_identity
from flask_bcrypt import Bcrypt
from config.db import get_db_connection
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Create the blueprint
usuarios_bp = Blueprint('usuarios', __name__)

# Initialize bcrypt
bcrypt = Bcrypt()

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email):
    """Validate email format using regex"""
    if not email or not EMAIL_REGEX.match(email):
        return False
    return True

def validate_password(password):
    """Validate password strength"""
    if not password:
        return False, "La contraseña es requerida"
    
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    
    if len(password) > 128:
        return False, "La contraseña es demasiado larga (máximo 128 caracteres)"
    
    # Check if password contains at least one letter and one number
    if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos una letra y un número"
    
    return True, "Válida"

def validate_nombre(nombre):
    """Validate name field"""
    if not nombre or not nombre.strip():
        return False, "El nombre es requerido"
    
    if len(nombre.strip()) < 2:
        return False, "El nombre debe tener al menos 2 caracteres"
    
    if len(nombre.strip()) > 50:
        return False, "El nombre es demasiado largo (máximo 50 caracteres)"
    
    # Check if name contains only letters, spaces, and common characters
    if not re.match(r'^[a-zA-ZÀ-ÿ\u00f1\u00d1\s\.\-\']+$', nombre.strip()):
        return False, "El nombre contiene caracteres no válidos"
    
    return True, "Válido"

@usuarios_bp.route('/registrar', methods=['POST'])
def registrar():
    try:
        # Obtain information from the body
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        
        nombre = data.get('nombre', '').strip() if data.get('nombre') else ''
        email = data.get('email', '').strip().lower() if data.get('email') else ''
        password = data.get('password', '')
        
        # Validate all required fields are present
        if not nombre or not email or not password:
            return jsonify({"error": "Todos los campos son requeridos (nombre, email, password)"}), 400
        
        # Validate nombre
        nombre_valid, nombre_message = validate_nombre(nombre)
        if not nombre_valid:
            return jsonify({"error": nombre_message}), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({"error": "El formato del email no es válido"}), 400
        
        # Validate password strength
        password_valid, password_message = validate_password(password)
        if not password_valid:
            return jsonify({"error": password_message}), 400
        
        # Obtain the cursor
        cursor = get_db_connection()
        
        if not cursor:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
        # Verify the user does not exist
        cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return jsonify({"error": "El usuario ya existe con este email"}), 409
        
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Insert the new user to the database
        cursor.execute(
            '''INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)''',
            (nombre, email, hashed_password)
        )
        
        cursor.connection.commit()
        
        return jsonify({
            "message": "Usuario registrado exitosamente",
            "user": {
                "nombre": nombre,
                "email": email
            }
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Error al registrar el usuario: {str(e)}"}), 500
    
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

@usuarios_bp.route('/login', methods=['POST'])
def login():
    try:
        # Obtain information from the body
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        
        email = data.get('email', '').strip().lower() if data.get('email') else ''
        password = data.get('password', '')
        
        # Validate required fields
        if not email or not password:
            return jsonify({"error": "Email y contraseña son requeridos"}), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({"error": "El formato del email no es válido"}), 400
        
        # Get database connection
        cursor = get_db_connection()
        
        if not cursor:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
        # Find user by email
        cursor.execute("SELECT id_usuario, nombre, email, password FROM usuarios WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"error": "Credenciales inválidas"}), 401
        
        # Verify password
        if not bcrypt.check_password_hash(user[3], password):  # user[3] is the password field
            return jsonify({"error": "Credenciales inválidas"}), 401
        
        # Create access token
        access_token = create_access_token(
            identity={
                "id_usuario": user[0],
                "email": user[2]
            }
        )
        
        return jsonify({
            "message": "Login exitoso",
            "access_token": access_token,
            "user": {
                "id_usuario": user[0],
                "nombre": user[1],
                "email": user[2]
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error al iniciar sesión: {str(e)}"}), 500
    
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

@usuarios_bp.route('/obtener', methods=['GET'])
@jwt_required()
def obtener_usuarios():
    try:
        # SOLUCIÓN: Manejar el token de forma más flexible
        try:
            # Intentar con get_jwt_identity() primero
            current_user_identity = get_jwt_identity()
        except Exception as e:
            # Si falla, intentar con get_jwt()
            try:
                jwt_data = get_jwt()
                current_user_identity = jwt_data.get('sub', {})
            except:
                current_user_identity = None
        
        # Debug: imprimir qué se recibió
        print(f"DEBUG - Tipo de identity: {type(current_user_identity)}")
        print(f"DEBUG - Identity: {current_user_identity}")
        
        # Manejar diferentes casos de identity
        current_user_id = None
        
        if current_user_identity is None:
            return jsonify({"error": "No se pudo obtener la identidad del token"}), 401
        
        elif isinstance(current_user_identity, dict):
            current_user_id = current_user_identity.get('id_usuario')
        
        elif isinstance(current_user_identity, (int, str)):
            current_user_id = current_user_identity
        
        else:
            # Si es otro tipo, convertirlo a string
            current_user_id = str(current_user_identity)
        
        # Obtener conexión a la base de datos
        cursor = get_db_connection()
        
        if not cursor:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
        # Obtener todos los usuarios (excluyendo passwords por seguridad)
        cursor.execute("SELECT id_usuario, nombre, email, fecha_creacion FROM usuarios")
        usuarios = cursor.fetchall()
        
        # Formatear los resultados
        usuarios_list = []
        for usuario in usuarios:
            usuarios_list.append({
                "id_usuario": usuario[0],
                "nombre": usuario[1],
                "email": usuario[2],
                "fecha_creacion": usuario[3].isoformat() if usuario[3] else None
            })
        
        return jsonify({
            "message": "Usuarios obtenidos exitosamente",
            "current_user_id": current_user_id,
            "usuarios": usuarios_list,
            "total": len(usuarios_list)
        }), 200
        
    except Exception as e:
        # Debug del error
        print(f"ERROR: {str(e)}")
        return jsonify({"error": f"Error al obtener los usuarios: {str(e)}"}), 500
    
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()