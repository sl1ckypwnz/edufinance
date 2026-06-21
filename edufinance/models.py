from datetime import datetime, timezone
from decimal import Decimal

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    users = db.relationship("User", back_populates="role")


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active_flag = db.Column(db.Boolean, default=True, nullable=False)

    role = db.relationship("Role", back_populates="users")
    accounts = db.relationship("Account", back_populates="user", cascade="all, delete-orphan")
    transactions = db.relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_active(self):
        return self.is_active_flag

    @property
    def is_admin(self):
        return self.role and self.role.name == "admin"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Account(db.Model):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(3), default="RUB", nullable=False)
    balance = db.Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", back_populates="accounts")
    transactions = db.relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="account", cascade="all, delete-orphan")


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    operation_type = db.Column(db.String(20), nullable=False)  # income / expense


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    operation_type = db.Column(db.String(20), nullable=False)  # income / expense
    amount = db.Column(Numeric(12, 2), nullable=False)
    comment = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = db.relationship("User", back_populates="transactions")
    account = db.relationship("Account", back_populates="transactions")
    category = db.relationship("Category")


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False, index=True)
    amount = db.Column(Numeric(12, 2), nullable=False)
    recipient = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default="created", nullable=False)  # created / confirmed / declined / cancelled
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", back_populates="payments")
    account = db.relationship("Account", back_populates="payments")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(120), nullable=False)
    details = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = db.relationship("User")
