from functools import wraps

from flask import abort
from flask_login import current_user

from edufinance.models import AuditLog, db


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            if current_user.is_authenticated:
                log_action(current_user.id, "forbidden_admin_access", "Attempt to open admin route")
            abort(403)
        return view_func(*args, **kwargs)

    return wrapper


def log_action(user_id, action: str, details: str | None = None) -> None:
    db.session.add(AuditLog(user_id=user_id, action=action, details=details))
    db.session.commit()
