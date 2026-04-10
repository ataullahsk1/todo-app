"""
app.py  ─  Entry point for the Todo application
─────────────────────────────────────────────────
Run with:
    python backend/app.py
"""

import os
import sys
import logging

# Allow imports like `from backend.models import ...`
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from flask_login import LoginManager

from backend.config import Config
from backend.models import db, User
from backend.auth import auth_bp
from backend.todos import todos_bp
from backend.reminder import start_scheduler

# ── Logging setup ──────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "frontend", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend", "static"),
    )

    # ── Load config ────────────────────────────
    app.config.from_object(Config)

    # ── Database ───────────────────────────────
    db.init_app(app)
    with app.app_context():
        db.create_all()
        logger.info("Database tables are ready.")

    # ── Login manager ──────────────────────────
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"
    login_manager.login_message = "Please log in to access your tasks."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Blueprints ─────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(todos_bp)

    # ── Background reminder scheduler ──────────
    start_scheduler(app)

    return app


if __name__ == "__main__":
    application = create_app()
    logger.info("Starting Todo App on http://127.0.0.1:5000")
    application.run(debug=True, use_reloader=False, host="127.0.0.1", port=5000)
