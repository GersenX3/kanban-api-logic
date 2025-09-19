from flask import Flask
from .db import db
from .routes import kanban_bp
from flask_migrate import Migrate
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://kanbanuser:supersecretpassword@postgres-kanban/kanbandb" # "postgresql://kanban:secret@localhost:5433/kanban_db" and  "postgresql://kanbanuser:supersecretpassword@postgres-kanban/kanbandb"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "super-secret-key"

    db.init_app(app)
    # Importar modelos para que estén disponibles para las migraciones
    from app.models import User, Board, Column, Task
    Migrate(app, db)
    CORS(
        app,
        resources={r"/*": {"origins": ["http://localhost:5173"]}},  # habilita solo para tu frontend
        supports_credentials=True
    )
    app.register_blueprint(kanban_bp, url_prefix="/kanban")

    return app
