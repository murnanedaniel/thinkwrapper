from flask import Flask
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def get_database_url():
    """Get database URL from environment."""
    url = os.getenv('DATABASE_URL', 'sqlite:///thinkwrapper.db')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="static")

    # Configure secret key for sessions
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Load configuration
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    # Initialize database
    database_url = get_database_url()
    engine = create_engine(database_url)

    from .models import Base
    Base.metadata.create_all(engine)

    app.db_session_factory = scoped_session(sessionmaker(bind=engine))
    app.config['DATABASE_URL'] = database_url

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        app.db_session_factory.remove()

    # Initialize OAuth
    from .auth import init_oauth, init_login_manager
    oauth_client = init_oauth(app)
    login_manager = init_login_manager(app)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        db = app.db_session_factory()
        return db.query(User).get(int(user_id))

    # Initialize Celery with Flask app context
    from app.celery_config import celery
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Register routes
    from . import routes
    app.register_blueprint(routes.bp)

    from . import auth_routes
    app.register_blueprint(auth_routes.auth_bp)

    # Health check
    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app
