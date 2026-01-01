import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="static")

    # Load configuration
    if test_config is None:
        env = os.environ.get("FLASK_ENV", "development")
        from .config import config

        app.config.from_object(config[env])
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config.get("CORS_ORIGINS", ["http://localhost:5173"]))
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Import models to register with SQLAlchemy
    from . import models

    # Register blueprints
    from . import routes

    app.register_blueprint(routes.bp)

    # Health check endpoint
    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app
