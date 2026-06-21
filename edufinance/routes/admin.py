from flask import Blueprint, render_template
from flask_login import login_required

from edufinance.models import Account, AuditLog, User
from edufinance.security import admin_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def panel():
    users = User.query.order_by(User.created_at.desc()).all()
    accounts = Account.query.order_by(Account.created_at.desc()).all()
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(50).all()
    return render_template("admin.html", users=users, accounts=accounts, logs=logs)
