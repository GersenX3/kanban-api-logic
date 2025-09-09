from flask import Blueprint, request, jsonify
from .models import User, Board, Column, Task
from .db import db

kanban_bp = Blueprint("kanban", __name__)

# --- Rutas para Tableros ---
# Ahora, las rutas asumen que la autenticación es manejada por un servicio externo
# y que el ID del usuario se pasa en un encabezado de la solicitud, por ejemplo, "X-User-ID".

@kanban_bp.route("/boards", methods=["POST"])
def create_board():
    # Obtiene el ID del usuario del encabezado de la solicitud
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"message": "Authorization header missing"}), 401
        
    data = request.get_json()
    name = data.get("name")

    if not name:
        return jsonify({"message": "Board name is required"}), 400

    new_board = Board(name=name, user_id=user_id)
    db.session.add(new_board)
    db.session.commit()
    return jsonify({"id": new_board.id, "name": new_board.name}), 201

@kanban_bp.route("/boards", methods=["GET"])
def get_boards():
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"message": "Authorization header missing"}), 401

    boards = Board.query.filter_by(user_id=user_id).all()
    boards_list = [{"id": b.id, "name": b.name} for b in boards]
    return jsonify(boards_list)

@kanban_bp.route("/boards/<int:board_id>", methods=["GET"])
def get_board(board_id):
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"message": "Authorization header missing"}), 401
        
    board = Board.query.filter_by(id=board_id, user_id=user_id).first_or_404()
    
    columns_data = []
    for column in sorted(board.columns, key=lambda c: c.position):
        tasks_data = [{"id": t.id, "title": t.title, "description": t.description, "position": t.position} for t in sorted(column.tasks, key=lambda t: t.position)]
        columns_data.append({"id": column.id, "name": column.name, "tasks": tasks_data})
        
    return jsonify({"id": board.id, "name": board.name, "columns": columns_data})

# --- Rutas para Columnas ---

@kanban_bp.route("/boards/<int:board_id>/columns", methods=["POST"])
def create_column(board_id):
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"message": "Authorization header missing"}), 401
        
    board = Board.query.filter_by(id=board_id, user_id=user_id).first_or_404()
    data = request.get_json()
    name = data.get("name")
    
    if not name:
        return jsonify({"message": "Column name is required"}), 400
        
    # Obtener la posición de la nueva columna (al final)
    max_position = db.session.query(db.func.max(Column.position)).filter_by(board_id=board_id).scalar() or -1
    new_position = max_position + 1

    new_column = Column(name=name, board_id=board.id, position=new_position)
    db.session.add(new_column)
    db.session.commit()
    return jsonify({"id": new_column.id, "name": new_column.name, "position": new_column.position}), 201

# --- Rutas para Tareas ---

@kanban_bp.route("/columns/<int:column_id>/tasks", methods=["POST"])
def create_task(column_id):
    # La validación de que la columna pertenezca al usuario se hace indirectamente a través del `board_id` en las otras rutas.
    # Por simplicidad, esta ruta asume que el `column_id` es válido.
    data = request.get_json()
    title = data.get("title")

    if not title:
        return jsonify({"message": "Task title is required"}), 400
    
    column = Column.query.get_or_404(column_id)
    
    # Obtener la posición de la nueva tarea (al final)
    max_position = db.session.query(db.func.max(Task.position)).filter_by(column_id=column_id).scalar() or -1
    new_position = max_position + 1

    new_task = Task(title=title, description=data.get("description"), position=new_position, column_id=column_id)
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"id": new_task.id, "title": new_task.title, "position": new_task.position}), 201

@kanban_bp.route("/tasks/<int:task_id>/move", methods=["PUT"])
def move_task(task_id):
    # Por simplicidad, esta ruta asume que el `task_id` es válido.
    data = request.get_json()
    new_column_id = data.get("new_column_id")
    new_position = data.get("new_position")

    task = Task.query.get_or_404(task_id)
    new_column = Column.query.get_or_404(new_column_id)
    
    # TODO: Añadir lógica para reordenar las tareas después del movimiento
    task.column_id = new_column_id
    task.position = new_position
    db.session.commit()
    return jsonify({"message": "Task moved successfully"})

# Más rutas para actualizar y eliminar tableros, columnas y tareas irían aquí.
