from flask import Flask
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from datetime import timedelta
from app.routes import bp as routes_bp
import os

# Extensions

jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # App configuration
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "default-jwt-key")
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1000)
    app.secret_key = os.getenv("APP_SECRET_KEY", "default-fallback-key")
    
    swagger_config_path = os.path.join(
            os.path.dirname(__file__), "swagger_docs", "swagger_config.yaml"
        )
    
    swagger = Swagger(app, template_file=swagger_config_path)
    # Initialize extensions
    jwt.init_app(app) 

    app.register_blueprint(routes_bp)

    return app
