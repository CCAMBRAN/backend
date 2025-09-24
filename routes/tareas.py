from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config.db import get_db_connection

# Crear el blueprint
tareas_bp = Blueprint('tareas', __name__)

# Crear un endpoint obtener tareas
@tareas_bp.route('/obtener', methods=['GET'])
@jwt_required()
def get():

    # Obtenemos la identidad del dueño del token
    current_user = get_jwt_identity()

    # Conectamos a la bd
    cursor = get_db_connection()

    # Ejecutar la consulta
    query = '''
               SELECT a.id_usuario, a.descripcion, b.nombre, b.email, a.creado_en
               FROM tareas as a 
               INNER JOIN usuarios as b on a.id_usuario = b.id_usuario
               WHERE a.id_usuario = %s
            '''
    
    cursor.execute(query, (current_user,))
    lista = cursor.fetchall()

    cursor.close()

    if not lista:
        return jsonify({"error":"El usuario no tiene tareas"}),404
    else:
        return jsonify({"lista":lista}),200

    

# Crear endpoint con post recibiendo datos desde el body
@tareas_bp.route('/crear', methods=['POST'])
@jwt_required()
def crear():

    # Obtener la identidad del dueño del token
    current_user = get_jwt_identity()

    # Obtener los datos del body
    data = request.get_json()
    descripcion = data.get('descripcion')

    if not descripcion:
        return jsonify({"error":"Debes teclear una descripcion"}),400
    
    # Obtenemos el cursor
    cursor = get_db_connection()

    # Hacemos el insert
    try:
        cursor.execute('INSERT INTO tareas (descripcion, id_usuario) values (%s, %s)', 
                       (descripcion,current_user))
        cursor.connection.commit()
        return jsonify({"message":"Tarea creada"}),201
    except Exception as e:
        return jsonify({"Error":f"No se pudo crear la tarea: {str(e)}"})
    finally:
        # Cierro el cursor y la conexion
        cursor.close()


# Crear endpoint usando PUT y pasando datos por el body y el url
@tareas_bp.route('/modificar/<int:id_tarea>', methods=['PUT'])
@jwt_required()
def modificar(id_tarea):

    # Obtenemos la identidad del dueño de la tarea
    current_user = get_jwt_identity()

    # Obtenemos los datos del body
    data = request.get_json()

    descripcion = data.get('descripcion')

    cursor = get_db_connection()

    # Verificamos si existe la tarea
    query = "SELECT * FROM tareas WHERE id_tarea = %s"
    cursor.execute(query, (id_tarea,))
    tarea = cursor.fetchone()
    #tarea = (1,2, .... n)

    # Verificamos que la tarea exista
    if not tarea:
        cursor.close()
        return jsonify({"error":"Esa tarea no existe"}), 404
    
    # Verificamos que la tarea pertenezca al usuario logueado
    if not tarea[1] == int(current_user):
        cursor.close()
        return jsonify({"error": "Credenciales Incorrectas"}), 401
    
    # Actualizar los datos
    try:
        cursor.execute("UPDATE tareas SET descripcion = %s WHERE id_tarea = %s", 
                       (descripcion, id_tarea))
        cursor.connection.commit()
        return jsonify({"mensaje":"Datos actualizados correctamenet"}),200
    except Exception as e:
        return jsonify({"error":f"Error al actualizar los datos: {str(e)}"})
    finally:
        cursor.close()
        

