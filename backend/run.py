import os
from dotenv import load_dotenv
from flask import Flask
from app.config.development import DevelopmentConfig
from app.config.production import ProductionConfig
from app.utils.logger import setup_logger
from app.api.base import bp as general_bp

def create_app(config_class=None):
    """Application factory function."""

    # Load environment variables from .env file
    load_dotenv()

    # Create Flask app instance
    app = Flask(__name__)

    # Configure app
    if config_class is None:
        config_class = ProductionConfig if os.getenv('FLASK_ENV') == 'production' else DevelopmentConfig
    app.config.from_object(config_class)

    # Set up logging
    setup_logger(app)

    # Register blueprints
    app.register_blueprint(general_bp, url_prefix=app.config['API_PREFIX'])

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
