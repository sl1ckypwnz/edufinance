import os
from datetime import datetime
from decimal import Decimal

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

from edufinance.models import Account, Category, Role, User, db

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Для доступа к странице необходимо войти в систему."


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///edufinance.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_TIME_LIMIT=None,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    from edufinance.routes.admin import admin_bp
    from edufinance.routes.auth import auth_bp
    from edufinance.routes.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_now():
        return {"current_year": datetime.now().year}

    @app.cli.command("init-db")
    def init_db_command():
        seed_database(app)
        print("Database initialized with demo data.")

    return app


def seed_database(app: Flask) -> None:
    with app.app_context():
        db.drop_all()
        db.create_all()

        admin_role = Role(name="admin", description="Administrator with extended access")
        user_role = Role(name="user", description="Regular application user")
        observer_role = Role(name="observer", description="Teacher / reviewer role")
        db.session.add_all([admin_role, user_role, observer_role])
        db.session.flush()

        categories = [
            Category(name="Зарплата", operation_type="income"),
            Category(name="Стипендия", operation_type="income"),
            Category(name="Подработка", operation_type="income"),
            Category(name="Продукты", operation_type="expense"),
            Category(name="Транспорт", operation_type="expense"),
            Category(name="Обучение", operation_type="expense"),
            Category(name="Платежи", operation_type="expense"),
        ]
        db.session.add_all(categories)

        admin = User(
            email=os.getenv("DEMO_ADMIN_EMAIL", "admin@example.com"),
            full_name="Demo Administrator",
            role=admin_role,
        )
        admin.set_password(os.getenv("DEMO_ADMIN_PASSWORD", "Admin12345!"))

        user = User(
            email=os.getenv("DEMO_USER_EMAIL", "user@example.com"),
            full_name="Demo User",
            role=user_role,
        )
        user.set_password(os.getenv("DEMO_USER_PASSWORD", "User12345!"))
        db.session.add_all([admin, user])
        db.session.flush()

        db.session.add(
            Account(user_id=user.id, name="Основной счет", currency="RUB", balance=Decimal("25000.00"))
        )
        db.session.commit()
