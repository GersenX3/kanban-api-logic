from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from .models import User, Board, Column, Task
from .db import db

kanban_bp = Blueprint("kanban", __name__)

# Para simplicidad, usaremos un user_id fijo o el primer usuario
# En un proyecto real podrías usar sesiones o cookies simples
def get_current_user():
    """
    Función simplificada para obtener el usuario actual.
    Opciones:
    1. Usar un user_id fijo (recomendado para portafolio/demo)
    2. Usar el primer usuario de la base de datos
    3. Crear un usuario por defecto si no existe
    """
    try:
        # Opción 1: User ID fijo para demo
        user_id = 1  # Cambiar por el ID del usuario que quieras usar
        
        # Opción 2: Usar el primer usuario disponible
        # user = User.query.first()
        # if not user:
        #     # Crear usuario por defecto si no existe
        #     user = User(username="demo_user", email="demo@example.com")
        #     db.session.add(user)
        #     db.session.commit()
        # user_id = user.id
        
        return user_id
    except Exception as e:
        print(f"Error getting current user: {e}")
        return 1  # Fallback a user_id = 1

# --- Rutas para Tableros ---

@kanban_bp.route("/boards", methods=["POST"])
def create_board():
    user_id = get_current_user()
        
    try:
        data = request.get_json()
        name = data.get("name", "").strip()

        if not name:
            return jsonify({"message": "Board name is required"}), 400

        new_board = Board(name=name, user_id=user_id)
        db.session.add(new_board)
        db.session.commit()
        
        return jsonify({
            "id": new_board.id, 
            "name": new_board.name,
            "created_at": new_board.created_at.isoformat() if hasattr(new_board, 'created_at') else None
        }), 201
        
    except SQLAlchemyError as e:
        print(f"Database error in create_board: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

@kanban_bp.route("/boards", methods=["GET"])
def get_boards():
    print("=== GET_BOARDS CALLED ===")
    user_id = get_current_user()
    print(f"Using User ID: {user_id}")

    try:
        boards = Board.query.filter_by(user_id=user_id).order_by(Board.created_at.desc()).all()
        print(f"Found {len(boards)} boards for user {user_id}")
        
        boards_list = [
            {
                "id": b.id, 
                "name": b.name,
                "created_at": b.created_at.isoformat() if hasattr(b, 'created_at') else None,
                "columns_count": len(b.columns)
            } for b in boards
        ]
        print("=== GET_BOARDS SUCCESS ===")
        return jsonify(boards_list)
    except SQLAlchemyError as e:
        print(f"Database error in get_boards: {e}")
        return jsonify({"message": "Database error occurred"}), 500

@kanban_bp.route("/boards/<int:board_id>", methods=["GET"])
def get_board(board_id):
    user_id = get_current_user()
    
    try:
        board = Board.query.filter_by(id=board_id, user_id=user_id).first_or_404()
        
        columns_data = []
        for column in sorted(board.columns, key=lambda c: c.position):
            tasks_data = [
                {
                    "id": t.id, 
                    "title": t.title, 
                    "description": t.description, 
                    "position": t.position,
                    "created_at": t.created_at.isoformat() if hasattr(t, 'created_at') else None,
                    "updated_at": t.updated_at.isoformat() if hasattr(t, 'updated_at') else None
                } 
                for t in sorted(column.tasks, key=lambda t: t.position)
            ]
            columns_data.append({
                "id": column.id, 
                "name": column.name, 
                "position": column.position,
                "tasks": tasks_data
            })
            
        return jsonify({
            "id": board.id, 
            "name": board.name, 
            "columns": columns_data,
            "created_at": board.created_at.isoformat() if hasattr(board, 'created_at') else None
        })
    except SQLAlchemyError as e:
        print(f"Database error in get_board: {e}")
        return jsonify({"message": "Database error occurred"}), 500

@kanban_bp.route("/boards/<int:board_id>", methods=["PUT"])
def update_board(board_id):
    user_id = get_current_user()
    
    try:
        board = Board.query.filter_by(id=board_id, user_id=user_id).first_or_404()
        data = request.get_json()
        name = data.get("name", "").strip()
        
        if not name:
            return jsonify({"message": "Board name is required"}), 400
        
        board.name = name
        if hasattr(board, 'updated_at'):
            from datetime import datetime
            board.updated_at = datetime.utcnow()
            
        db.session.commit()
        return jsonify({
            "id": board.id, 
            "name": board.name,
            "message": "Board updated successfully"
        })
    except SQLAlchemyError as e:
        print(f"Database error in update_board: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

@kanban_bp.route("/boards/<int:board_id>", methods=["DELETE"])
def delete_board(board_id):
    user_id = get_current_user()
    
    try:
        board = Board.query.filter_by(id=board_id, user_id=user_id).first_or_404()
        db.session.delete(board)
        db.session.commit()
        return jsonify({"message": "Board deleted successfully"})
    except SQLAlchemyError as e:
        print(f"Database error in delete_board: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

# --- Rutas para Columnas ---

@kanban_bp.route("/boards/<int:board_id>/columns", methods=["POST"])
def create_column(board_id):
    user_id = get_current_user()
        
    try:
        board = Board.query.filter_by(id=board_id, user_id=user_id).first_or_404()
        data = request.get_json()
        name = data.get("name", "").strip()
        
        if not name:
            return jsonify({"message": "Column name is required"}), 400
            
        # Obtener la posición de la nueva columna (al final)
        max_position = db.session.query(db.func.max(Column.position)).filter_by(board_id=board_id).scalar() or -1
        new_position = max_position + 1

        new_column = Column(name=name, board_id=board.id, position=new_position)
        db.session.add(new_column)
        db.session.commit()
        
        return jsonify({
            "id": new_column.id, 
            "name": new_column.name, 
            "position": new_column.position,
            "board_id": new_column.board_id
        }), 201
    except SQLAlchemyError as e:
        print(f"Database error in create_column: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

@kanban_bp.route("/columns/<int:column_id>", methods=["PUT"])
def update_column(column_id):
    user_id = get_current_user()
    
    try:
        # Verificar que la columna pertenezca al usuario
        column = db.session.query(Column).join(Board).filter(
            Column.id == column_id,
            Board.user_id == user_id
        ).first_or_404()
        
        data = request.get_json()
        name = data.get("name", "").strip()
        
        if not name:
            return jsonify({"message": "Column name is required"}), 400
        
        column.name = name
        db.session.commit()
        
        return jsonify({
            "id": column.id,
            "name": column.name,
            "message": "Column updated successfully"
        })
    except SQLAlchemyError as e:
        print(f"Database error in update_column: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

@kanban_bp.route("/columns/<int:column_id>", methods=["DELETE"])
def delete_column(column_id):
    user_id = get_current_user()
    
    try:
        # Verificar que la columna pertenezca al usuario
        column = db.session.query(Column).join(Board).filter(
            Column.id == column_id,
            Board.user_id == user_id
        ).first_or_404()
        
        db.session.delete(column)
        db.session.commit()
        return jsonify({"message": "Column deleted successfully"})
    except SQLAlchemyError as e:
        print(f"Database error in delete_column: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

@kanban_bp.route("/boards/<int:board_id>/columns/reorder", methods=["PUT"])
def reorder_columns(board_id):
    user_id = get_current_user()
    
    try:
        board = Board.query.filter_by(id=board_id, user_id=user_id).first_or_404()
        data = request.get_json()
        column_orders = data.get("column_orders", [])  # [{"id": 1, "position": 0}, ...]
        
        for order_data in column_orders:
            column = Column.query.filter_by(id=order_data["id"], board_id=board_id).first()
            if column:
                column.position = order_data["position"]
        
        db.session.commit()
        return jsonify({"message": "Columns reordered successfully"})
    except SQLAlchemyError as e:
        print(f"Database error in reorder_columns: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

# --- Rutas para Tareas ---

@kanban_bp.route("/columns/<int:column_id>/tasks", methods=["POST"])
def create_task(column_id):
    user_id = get_current_user()
    
    try:
        # Verificar que la columna pertenezca al usuario
        column = db.session.query(Column).join(Board).filter(
            Column.id == column_id,
            Board.user_id == user_id
        ).first_or_404()
        
        data = request.get_json()
        title = data.get("title", "").strip()

        if not title:
            return jsonify({"message": "Task title is required"}), 400
        
        # Obtener la posición de la nueva tarea (al final)
        max_position = db.session.query(db.func.max(Task.position)).filter_by(column_id=column_id).scalar() or -1
        new_position = max_position + 1

        new_task = Task(
            title=title, 
            description=data.get("description", ""), 
            position=new_position, 
            column_id=column_id
        )
        db.session.add(new_task)
        db.session.commit()
        
        return jsonify({
            "id": new_task.id, 
            "title": new_task.title,
            "description": new_task.description,
            "position": new_task.position,
            "column_id": new_task.column_id,
            "created_at": new_task.created_at.isoformat() if hasattr(new_task, 'created_at') else None
        }), 201
    except SQLAlchemyError as e:
        print(f"Database error in create_task: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

@kanban_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    user_id = get_current_user()
    
    try:
        # Verificar que la tarea pertenezca al usuario
        task = db.session.query(Task).join(Column).join(Board).filter(
            Task.id == task_id,
            Board.user_id == user_id
        ).first_or_404()
        
        data = request.get_json()
        title = data.get("title", "").strip()
        
        if not title:
            return jsonify({"message": "Task title is required"}), 400
        
        task.title = title
        task.description = data.get("description", "")
        
        if hasattr(task, 'updated_at'):
            from datetime import datetime
            task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "message": "Task updated successfully"
        })
    except SQLAlchemyError as e:
        print(f"Database error in update_task: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

@kanban_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    user_id = get_current_user()
    
    try:
        # Verificar que la tarea pertenezca al usuario
        task = db.session.query(Task).join(Column).join(Board).filter(
            Task.id == task_id,
            Board.user_id == user_id
        ).first_or_404()
        
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Task deleted successfully"})
    except SQLAlchemyError as e:
        print(f"Database error in delete_task: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

@kanban_bp.route("/tasks/<int:task_id>/move", methods=["PUT"])
def move_task(task_id):
    user_id = get_current_user()
    
    try:
        # Verificar que la tarea pertenezca al usuario
        task = db.session.query(Task).join(Column).join(Board).filter(
            Task.id == task_id,
            Board.user_id == user_id
        ).first_or_404()
        
        data = request.get_json()
        new_column_id = data.get("new_column_id")
        new_position = data.get("new_position")

        if new_column_id is None or new_position is None:
            return jsonify({"message": "new_column_id and new_position are required"}), 400

        # Verificar que la nueva columna pertenezca al mismo usuario
        new_column = db.session.query(Column).join(Board).filter(
            Column.id == new_column_id,
            Board.user_id == user_id
        ).first_or_404()
        
        old_column_id = task.column_id
        old_position = task.position
        
        # Si se mueve dentro de la misma columna, reordenar las tareas
        if old_column_id == new_column_id:
            # Reordenar tareas en la misma columna
            if new_position < old_position:
                # Mover hacia arriba: incrementar posición de tareas entre new_position y old_position-1
                tasks_to_update = Task.query.filter(
                    Task.column_id == old_column_id,
                    Task.position >= new_position,
                    Task.position < old_position
                ).all()
                for t in tasks_to_update:
                    t.position += 1
            else:
                # Mover hacia abajo: decrementar posición de tareas entre old_position+1 y new_position
                tasks_to_update = Task.query.filter(
                    Task.column_id == old_column_id,
                    Task.position > old_position,
                    Task.position <= new_position
                ).all()
                for t in tasks_to_update:
                    t.position -= 1
        else:
            # Movimiento entre columnas diferentes
            # Decrementar posición de tareas después de la posición original en la columna antigua
            tasks_old_column = Task.query.filter(
                Task.column_id == old_column_id,
                Task.position > old_position
            ).all()
            for t in tasks_old_column:
                t.position -= 1
            
            # Incrementar posición de tareas desde new_position en adelante en la nueva columna
            tasks_new_column = Task.query.filter(
                Task.column_id == new_column_id,
                Task.position >= new_position
            ).all()
            for t in tasks_new_column:
                t.position += 1
        
        # Actualizar la tarea movida
        task.column_id = new_column_id
        task.position = new_position
        
        if hasattr(task, 'updated_at'):
            from datetime import datetime
            task.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({
            "message": "Task moved successfully",
            "task": {
                "id": task.id,
                "title": task.title,
                "column_id": task.column_id,
                "position": task.position
            }
        })
    except SQLAlchemyError as e:
        print(f"Database error in move_task: {e}")
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500

# --- Ruta para obtener estadísticas del usuario ---

@kanban_bp.route("/stats", methods=["GET"])
def get_user_stats():
    print("=== GET_USER_STATS CALLED ===")
    user_id = get_current_user()
    
    try:
        boards_count = Board.query.filter_by(user_id=user_id).count()
        columns_count = db.session.query(Column).join(Board).filter(Board.user_id == user_id).count()
        tasks_count = db.session.query(Task).join(Column).join(Board).filter(Board.user_id == user_id).count()
        
        print(f"Stats for user {user_id}: {boards_count} boards, {columns_count} columns, {tasks_count} tasks")
        print("=== GET_USER_STATS SUCCESS ===")
        
        return jsonify({
            "boards_count": boards_count,
            "columns_count": columns_count,
            "tasks_count": tasks_count
        })
    except SQLAlchemyError as e:
        print(f"Database error in get_user_stats: {e}")
        return jsonify({"message": "Database error occurred"}), 500

# --- Ruta para sincronización completa ---

@kanban_bp.route("/sync", methods=["GET"])
def sync_all_data():
    user_id = get_current_user()
    
    try:
        boards = Board.query.filter_by(user_id=user_id).all()
        sync_data = []
        
        for board in boards:
            board_data = {
                "id": board.id,
                "name": board.name,
                "created_at": board.created_at.isoformat() if hasattr(board, 'created_at') else None,
                "updated_at": board.updated_at.isoformat() if hasattr(board, 'updated_at') else None,
                "columns": []
            }
            
            for column in sorted(board.columns, key=lambda c: c.position):
                column_data = {
                    "id": column.id,
                    "name": column.name,
                    "position": column.position,
                    "tasks": []
                }
                
                for task in sorted(column.tasks, key=lambda t: t.position):
                    task_data = {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "position": task.position,
                        "created_at": task.created_at.isoformat() if hasattr(task, 'created_at') else None,
                        "updated_at": task.updated_at.isoformat() if hasattr(task, 'updated_at') else None
                    }
                    column_data["tasks"].append(task_data)
                
                board_data["columns"].append(column_data)
            
            sync_data.append(board_data)
        
        return jsonify({
            "boards": sync_data,
            "sync_timestamp": db.func.now()
        })
    except SQLAlchemyError as e:
        print(f"Database error in sync_all_data: {e}")
        return jsonify({"message": "Database error occurred"}), 500