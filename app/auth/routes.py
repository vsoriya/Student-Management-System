from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Enrollment, Student, User
from app.students.forms import student_payload, validate_student
from app.utils import active_term
from .forms import validate_register_form

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
        student_data = student_payload(request.form)
        errors.extend(validate_student(student_data))
        if User.query.filter_by(email=email).first():
            errors.append("អ៊ីមែលនេះមានរួចហើយ។")
        if Student.query.filter_by(student_code=student_data["student_code"]).first():
            errors.append("លេខកូដសិស្សនេះមានរួចហើយ។")
        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            user = User(
                name=request.form["name"].strip(),
                email=email,
                role="student",
            )
            user.set_password(request.form["password"])
            student_data["class_id"] = None
            student = Student(**student_data, user=user)
            enrollment = Enrollment(student=student, status="Pending", term=active_term())
            db.session.add(user)
            db.session.add(student)
            db.session.add(enrollment)
            db.session.commit()
            flash("បានបង្កើតគណនីរួចរាល់។ សូមរង់ចាំ admin approve ការចុះឈ្មោះចូលរៀន។", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
