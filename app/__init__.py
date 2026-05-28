from flask import Flask
from config import Config
from app.extensions import db, migrate

def create_app(config_class=Config, test_config=None):

    app = Flask(__name__)
    app.config.from_object(config_class)
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db) # render_as_batch=True if SQLite

    from app.routes import api_bp
    app.register_blueprint(api_bp)

    from app.cli import seed_tickers_command
    app.cli.add_command(seed_tickers_command) # type: ignore

    return app