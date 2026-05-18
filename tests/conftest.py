import pytest
from app import create_app
from app.extensions import db

@pytest.fixture
def app():

    # Pass test configs to the app factory
    app = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    # Set up the database tables before the test runs
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    # Returns a pseudo-Postman client that can make simulated
    # requests to the app.
    return app.test_client()