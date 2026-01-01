from flask import Flask

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='static')
    
    # Load configuration
    if test_config is None:
        # Load the instance config when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
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
    
    # A simple route to check if the app is running
    @app.route('/health')
    def health():
        return {'status': 'ok'}
        
    return app 