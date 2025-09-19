from flask import Blueprint, request, jsonify
from config.db import get_db_connection

# create blueprint
tareas_bp = Blueprint('tareas', __name__)


@tareas_bp.route('/obtener', methods=['GET'])
def obtener_tareas():
    """Return tareas optionally filtered by usuario_id."""
    usuario_id = request.args.get('usuario_id', type=int)
    cursor = get_db_connection()

    if not cursor:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        if usuario_id is not None:
            cursor.execute(
                '''SELECT t.id, t.descripcion, t.creada_en, t.usuario_id, u.nombre
                   FROM tareas t
                   JOIN usuarios u ON t.usuario_id = u.id
                   WHERE t.usuario_id = %s
                   ORDER BY t.creada_en DESC''',
                (usuario_id,)
            )
        else:
            cursor.execute(
                '''SELECT t.id, t.descripcion, t.creada_en, t.usuario_id, u.nombre
                   FROM tareas t
                   JOIN usuarios u ON t.usuario_id = u.id
                   ORDER BY t.creada_en DESC'''
            )

        tareas = cursor.fetchall()

        tareas_list = [
            {
                "id": tarea[0],
                "descripcion": tarea[1],
                "creada_en": tarea[2].isoformat() if tarea[2] else None,
                "usuario_id": tarea[3],
                "usuario_nombre": tarea[4]
            }
            for tarea in tareas
        ]

        return jsonify({"tareas": tareas_list}), 200
    except Exception as e:
        return jsonify({"error": f"No se pudieron obtener las tareas: {str(e)}"}), 500
    finally:
        cursor.close()


@tareas_bp.route('/crear', methods=['POST'])
def crear():
    """Create a new tarea associated to an existing usuario."""
    data = request.get_json() or {}

    descripcion = data.get('descripcion', '').strip()
    usuario_id = data.get('usuario_id')

    if not descripcion:
        return jsonify({"error": "Debes proporcionar una descripción para la tarea"}), 400

    if not usuario_id:
        return jsonify({"error": "Debes proporcionar el usuario_id de la tarea"}), 400

    cursor = get_db_connection()

    if not cursor:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor.execute('SELECT id FROM usuarios WHERE id = %s', (usuario_id,))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({"error": "El usuario especificado no existe"}), 404

        cursor.execute(
            'INSERT INTO tareas (descripcion, usuario_id) VALUES (%s, %s)',
            (descripcion, usuario_id)
        )
        cursor.connection.commit()

        return jsonify({
            "message": "Tarea creada exitosamente",
            "tarea": {
                "id": cursor.lastrowid,
                "descripcion": descripcion,
                "usuario_id": usuario_id
            }
        }), 201
    except Exception as e:
        cursor.connection.rollback()
        return jsonify({"error": f"No se pudo crear la tarea: {str(e)}"}), 500
    finally:
        cursor.close()


@tareas_bp.route('/modificar/<int:tarea_id>', methods=['PUT'])
def modificar(tarea_id):
    """Update an existing tarea's descripcion."""
    data = request.get_json() or {}
    descripcion = data.get('descripcion', '').strip()

    if not descripcion:
        return jsonify({"error": "Debes proporcionar una descripción para actualizar la tarea"}), 400

    cursor = get_db_connection()

    if not cursor:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor.execute('SELECT id FROM tareas WHERE id = %s', (tarea_id,))
        tarea = cursor.fetchone()

        if not tarea:
            return jsonify({"error": "La tarea especificada no existe"}), 404

        cursor.execute('UPDATE tareas SET descripcion = %s WHERE id = %s', (descripcion, tarea_id))
        cursor.connection.commit()

        return jsonify({
            "message": "Tarea actualizada exitosamente",
            "tarea": {
                "id": tarea_id,
                "descripcion": descripcion
            }
        }), 200
    except Exception as e:
        cursor.connection.rollback()
        return jsonify({"error": f"No se pudo actualizar la tarea: {str(e)}"}), 500
    finally:
        cursor.close()