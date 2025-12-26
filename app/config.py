import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Default to SQLite for local ease, overridden by child classes
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///notefy.db")

class ProductionConfig(Config):
    """Production configuration"""
    # In production, we expect DATABASE_URL to be set (e.g., to Postgres)
    pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    # GitHub Actions provides the DATABASE_URL for Postgres
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False