
from flask import Blueprint, request, jsonify
from config.db import get_db_connection

tareas_bp = Blueprint('tareas', __name__)

@tareas_bp.route('/obtener', methods=['GET'])
def get():
    return jsonify({'message': 'Estas son las tareas uwu'}), 200

#crear endpoint con post recibiendo datos desde body

@tareas_bp.route('/crear', methods=['POST'])
def crear():
    data = request.get_json()
    descripcion = data.get('descripcion')

    if not descripcion:
        return jsonify({'error': 'La descripcion es requerida'}), 400
    
    cursor = get_db_connection()

    try:
        cursor.execute('INSERT INTO tareas (descripcion) VALUES (%s)', (descripcion,))
        cursor.connection.commit()  
        return jsonify({'message': 'Tarea creada exitosamente'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500    
    finally:
        cursor.close()
#crear endpoint con put recibiendo datos desde body y url

@tareas_bp.route('/actualizar/<int:user_id>', methods=['PUT'])
def actualizar(user_id):
    data = request.get_json()
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    
    return jsonify({'message': f'Tarea actualizada de {nombre} {apellido}', 'data': data}), 200
