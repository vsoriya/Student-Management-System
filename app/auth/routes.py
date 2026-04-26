from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import User
from .forms import ROLES, validate_register_form

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("students.dashboard"))
    if request.method == "POST":
        try:
            user = User.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        except SQLAlchemyError:
            flash("ប្រព័ន្ធមិនអាចភ្ជាប់ទៅ Database បានទេ។ សូមពិនិត្យ DATABASE_URL និងបង្កើតតារាង Database នៅលើ Server។", "danger")
            return render_template("login.html"), 503
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("students.dashboard"))
        flash("អ៊ីមែល ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ។", "danger")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        errors = validate_register_form(request.form)
        email = request.form.get("email", "").strip().lower()
        if User.query.filter_by(email=email).first():
            errors.append("អ៊ីមែលនេះមានរួចហើយ។")
        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            user = User(
                name=request.form["name"].strip(),
                email=email,
                role=request.form.get("role", "student"),
            )
            user.set_password(request.form["password"])
            db.session.add(user)
            db.session.commit()
            flash("បានបង្កើតគណនីរួចរាល់។ សូមចូលប្រើប្រាស់។", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html", roles=ROLES)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
