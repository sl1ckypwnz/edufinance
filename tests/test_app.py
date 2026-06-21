from edufinance import create_app
from edufinance.models import db


def test_app_redirects_to_login():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
        }
    )
    with app.app_context():
        db.create_all()

    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
