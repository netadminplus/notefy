"""
Notefy - Flask Application Factory
Production-grade note-taking application
"""

import logging
import sys
import json
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_flask_exporter import PrometheusMetrics

db = SQLAlchemy()
migrate = Migrate()


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging():
    """Configure structured JSON logging to stdout"""
    # Prevent duplicate handlers if create_app is called multiple times (like in tests)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        root_logger.addHandler(handler)


def create_app(config_name="production"):
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    if config_name == "testing":
        app.config.from_object("app.config.TestingConfig")
    elif config_name == "development":
        app.config.from_object("app.config.DevelopmentConfig")
    else:
        app.config.from_object("app.config.ProductionConfig")

    # Setup structured logging
    setup_logging()

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize Prometheus metrics
    metrics = PrometheusMetrics(app)
    metrics.info("notefy_app_info", "Notefy Application Info", version="1.0.0", environment=config_name)

    # Register blueprints and models
    with app.app_context():
        # IMPORT MODELS HERE so db.create_all() knows they exist
        from app import models 
        
        from app.routes import main_bp
        app.register_blueprint(main_bp)
        
        # Create tables
        db.create_all()

    app.logger.info(
        "Notefy application started",
        extra={"environment": config_name},
    )

    return app