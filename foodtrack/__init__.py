from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv

load_dotenv()  # read the .env file

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # configurations
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback_secrete")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///foodtrack.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # email configurations
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

    # initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # configure login manager (where to redirect for login)
    login_manager.login_view = "main.login"

    from foodtrack.routes import main

    # register blueprints
    app.register_blueprint(main)

    # create database tables
    with app.app_context():
        db.create_all()

    # return the app instance
    return app
