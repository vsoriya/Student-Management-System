from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import Teacher
from app.utils import roles_required, write_audit

teachers_bp = Blueprint("teachers", __name__, url_prefix="/teachers")


@teachers_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def list_teachers():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("សូមបញ្ចូលឈ្មោះគ្រូ។", "danger")
        else:
            teacher = Teacher(
                name=name,
                email=request.form.get("email", "").strip() or None,
                phone=request.form.get("phone", "").strip(),
                specialty=request.form.get("specialty", "").strip(),
            )
            db.session.add(teacher)
            db.session.flush()
            write_audit("create", "teacher", teacher.id, teacher.name)
            db.session.commit()
            flash("បានបង្កើតគ្រូរួចរាល់។", "success")
            return redirect(url_for("teachers.list_teachers"))
    return render_template("teachers/list.html", teachers=Teacher.query.order_by(Teacher.name).all())


@teachers_bp.route("/<int:teacher_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    write_audit("delete", "teacher", teacher.id, teacher.name)
    db.session.delete(teacher)
    db.session.commit()
    flash("បានលុបគ្រូរួចរាល់។", "success")
    return redirect(url_for("teachers.list_teachers"))
