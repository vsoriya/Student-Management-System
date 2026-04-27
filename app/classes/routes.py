from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import ClassRoom
from app.models import Teacher
from app.utils import roles_required, write_audit

classes_bp = Blueprint("classes", __name__, url_prefix="/classes")


@classes_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def list_classes():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        grade = request.form.get("grade", "").strip()
        if name and grade:
            room = ClassRoom(name=name, grade=grade, teacher_id=request.form.get("teacher_id") or None)
            db.session.add(room)
            db.session.flush()
            write_audit("create", "class", room.id, str(room))
            db.session.commit()
            flash("បានបង្កើតថ្នាក់រួចរាល់។", "success")
            return redirect(url_for("classes.list_classes"))
        flash("សូមបញ្ចូលឈ្មោះថ្នាក់ និងកម្រិតថ្នាក់។", "danger")
    return render_template("classes/list.html", classes=ClassRoom.query.order_by(ClassRoom.grade, ClassRoom.name).all(), teachers=Teacher.query.order_by(Teacher.name).all())


@classes_bp.route("/<int:class_id>/update", methods=["POST"])
@login_required
@roles_required("admin")
def update_class(class_id):
    class_room = ClassRoom.query.get_or_404(class_id)
    name = request.form.get("name", "").strip()
    grade = request.form.get("grade", "").strip()
    if not name or not grade:
        flash("សូមបញ្ចូលឈ្មោះថ្នាក់ និងកម្រិតថ្នាក់។", "danger")
        return redirect(url_for("classes.list_classes"))
    class_room.name = name
    class_room.grade = grade
    class_room.teacher_id = request.form.get("teacher_id") or None
    write_audit("update", "class", class_room.id, str(class_room))
    db.session.commit()
    flash("បានកែប្រែថ្នាក់រួចរាល់។", "success")
    return redirect(url_for("classes.list_classes"))


@classes_bp.route("/<int:class_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_class(class_id):
    class_room = ClassRoom.query.get_or_404(class_id)
    write_audit("delete", "class", class_room.id, str(class_room))
    db.session.delete(class_room)
    db.session.commit()
    flash("បានលុបថ្នាក់រួចរាល់។", "success")
    return redirect(url_for("classes.list_classes"))
