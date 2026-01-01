"""Flask application configuration."""

import os
from datetime import timedelta


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://localhost:5432/thinkwrapper"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }

    # Celery
    CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # API Keys (will be required in production)
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    BRAVE_SEARCH_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY")
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

    # Paddle
    PADDLE_VENDOR_ID = os.environ.get("PADDLE_VENDOR_ID")
    PADDLE_API_KEY = os.environ.get("PADDLE_API_KEY")
    PADDLE_PUBLIC_KEY = os.environ.get("PADDLE_PUBLIC_KEY")
    PADDLE_WEBHOOK_SECRET = os.environ.get("PADDLE_WEBHOOK_SECRET")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_DISCOVERY_URL = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )

    # Session
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Security
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously in tests


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False

    @classmethod
    def validate_config(cls):
        """Validate that required production config is present."""
        required = [
            "SECRET_KEY",
            "DATABASE_URL",
            "ANTHROPIC_API_KEY",
            "SENDGRID_API_KEY",
            "PADDLE_VENDOR_ID",
            "PADDLE_API_KEY",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
        ]
        missing = [key for key in required if not os.environ.get(key)]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
