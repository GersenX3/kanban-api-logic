from flask import Flask
from flask_jwt_extended import JWTManager
from .db import db
from .routes import kanban_bp
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://kanbanuser:supersecretpassword@postgres-kanban/kanbandb"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "super-secret-key"

    db.init_app(app)
    JWTManager(app)
    Migrate(app, db)

    app.register_blueprint(kanban_bp, url_prefix="/kanban")

    return app
