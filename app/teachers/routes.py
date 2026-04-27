from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import Teacher, User
from app.utils import roles_required, write_audit

teachers_bp = Blueprint("teachers", __name__, url_prefix="/teachers")


@teachers_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def list_teachers():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name:
            flash("សូមបញ្ចូលឈ្មោះគ្រូ។", "danger")
        elif not email:
            flash("សូមបញ្ចូលអ៊ីមែលគ្រូ។", "danger")
        elif len(password) < 6:
            flash("ពាក្យសម្ងាត់គ្រូត្រូវមានយ៉ាងហោចណាស់ ៦ តួអក្សរ។", "danger")
        elif User.query.filter_by(email=email).first():
            flash("អ៊ីមែលនេះមានគណនីរួចហើយ។", "danger")
        else:
            user = User(name=name, email=email, role="teacher")
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            teacher = Teacher(
                user_id=user.id,
                name=name,
                email=email,
                phone=request.form.get("phone", "").strip(),
                specialty=request.form.get("specialty", "").strip(),
            )
            db.session.add(teacher)
            db.session.flush()
            write_audit("create", "teacher", teacher.id, teacher.name)
            db.session.commit()
            flash("បានបង្កើតគ្រូ និងគណនី login រួចរាល់។", "success")
            return redirect(url_for("teachers.list_teachers"))
    return render_template("teachers/list.html", teachers=Teacher.query.order_by(Teacher.name).all())


@teachers_bp.route("/<int:teacher_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    user = teacher.user
    write_audit("delete", "teacher", teacher.id, teacher.name)
    db.session.delete(teacher)
    if user and user.role == "teacher":
        db.session.delete(user)
    db.session.commit()
    flash("បានលុបគ្រូរួចរាល់។", "success")
    return redirect(url_for("teachers.list_teachers"))
