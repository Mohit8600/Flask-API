from flask import Flask
from config import config
from app.routes import register_routes
from flask_jwt_extended import JWTManager

def create_app():
  app = Flask(__name__)


  jwt = JWTManager(app)
  
  app.config.from_object(config)
  app.config['JWT_SECRET_KEY'] = 'temp'
  register_routes(app)

  return app