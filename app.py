from flask import Flask

from config import Config
from controllers.auth_controller import auth_bp
from controllers.health_controller import health_bp
from controllers.post_controller import post_bp
from database.session import init_database
from services.file_service import ensure_upload_directories


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    init_database()
    ensure_upload_directories()

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(post_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
