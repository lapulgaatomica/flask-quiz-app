from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_bootstrap import Bootstrap
from flask_login import LoginManager

db = SQLAlchemy()
bootstrap = Bootstrap()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_name):
    """
    Ensures all the necessary installed packages are initialised

    :return: the flask app instance
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    config[config_name].init_app(app)
    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)

    if app.config['SSL_REDIRECT']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
