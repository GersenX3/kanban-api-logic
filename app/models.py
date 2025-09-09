from .db import db
from datetime import datetime

# El modelo original de User parece ser un modelo de Tarea. Lo corregiremos para ser un User real.

class User(db.Model):
    __tablename__ = "data_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Relación: Un usuario puede tener varios tableros.
    boards = db.relationship("Board", backref="owner", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"

class Board(db.Model):
    __tablename__ = "data_boards"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("data_users.id"), nullable=False)
    
    # Relación: Un tablero tiene varias columnas.
    columns = db.relationship("Column", backref="board", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Board {self.name}>"

class Column(db.Model):
    __tablename__ = "data_columns"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    board_id = db.Column(db.Integer, db.ForeignKey("data_boards.id"), nullable=False)

    # Relación: Una columna tiene varias tareas.
    tasks = db.relationship("Task", backref="column", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Column {self.name}>"

class Task(db.Model):
    __tablename__ = "data_tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    column_id = db.Column(db.Integer, db.ForeignKey("data_columns.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Task {self.title}>"
