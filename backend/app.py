from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config.config import Config

# Initialize SQLAlchemy globally
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Import and register your blueprints
    from routes.pomodoro import pomodoro_bp
    from routes.preferences import preferences_bp

    app.register_blueprint(pomodoro_bp)
    app.register_blueprint(preferences_bp)
   
    # Create database tables (executed only once)
    with app.app_context():
        db.create_all()

    return app

# Main entry point
app = create_app()

if __name__ == "__main__":
    app.run()
