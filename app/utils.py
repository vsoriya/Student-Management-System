from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user

from .extensions import db
from .models import AuditLog


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def write_audit(action, entity, entity_id=None, message=None):
    if current_user.is_authenticated:
        db.session.add(
            AuditLog(
                user_id=current_user.id,
                action=action,
                entity=entity,
                entity_id=entity_id,
                message=message,
            )
        )


def current_student_profile():
    if not current_user.is_authenticated or current_user.role != "student":
        return None

    from sqlalchemy import or_
    from .models import Student

    linked_student = Student.query.filter_by(user_id=current_user.id).first()
    if linked_student:
        return linked_student

    return Student.query.filter(
        or_(
            Student.student_code == current_user.email.split("@")[0],
            Student.name == current_user.name,
            Student.phone == current_user.email,
        )
    ).first()
