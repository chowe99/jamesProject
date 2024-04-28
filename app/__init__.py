from flask import Flask
from .config import Config
from openai import OpenAI

class CustomFlask(Flask):
    openai_client: OpenAI  # More specific typing for the OpenAI client

def create_app() -> CustomFlask:
    app = CustomFlask(__name__, static_folder='/app/app/static')
    app.config.from_object(Config)
    app.openai_client = OpenAI(api_key=app.config['OPENAI_API_KEY'])

    print("OpenAI API Key:", app.config['OPENAI_API_KEY'])
    print("Static folder:", app.static_folder)
    # Register blueprints and other app configurations
    from .routes import main_blueprint
    app.register_blueprint(main_blueprint, url_prefix='/')
    
    return app

