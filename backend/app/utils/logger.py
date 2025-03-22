import os
import logging
from logging.handlers import RotatingFileHandler
from flask import current_app

def setup_logger(app):
    """Configure logging for the application."""

    # Create logs directory if it doesn't exist
    log_dir = app.config['LOG_DIR']
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Set up file handler
    log_file = os.path.join(log_dir, 'app.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=app.config['LOG_MAX_BYTES'],
        backupCount=app.config['LOG_BACKUP_COUNT']
    )

    # Set log format
    formatter = logging.Formatter(app.config['LOG_FORMAT'])
    file_handler.setFormatter(formatter)

    # Set log level
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper())
    file_handler.setLevel(log_level)

    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)

    # Log application startup
    app.logger.info('Application startup complete')

def get_logger(name):
    """Get a logger instance for the given name."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        # If running in Flask context, use app config
        if current_app:
            log_level = getattr(logging, current_app.config['LOG_LEVEL'].upper())
            formatter = logging.Formatter(current_app.config['LOG_FORMAT'])
        else:
            # Default config for when running outside Flask context
            log_level = logging.INFO
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)

        logger.addHandler(console_handler)
        logger.setLevel(log_level)

    return logger
