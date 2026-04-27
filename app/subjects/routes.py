from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Subject
from app.models import Teacher
from app.utils import roles_required, write_audit

subjects_bp = Blueprint("subjects", __name__, url_prefix="/subjects")


@subjects_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def list_subjects():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            subject = Subject(name=name, teacher_id=request.form.get("teacher_id") or None)
            db.session.add(subject)
            try:
                db.session.flush()
                write_audit("create", "subject", subject.id, subject.name)
                db.session.commit()
                flash("បានបង្កើតមុខវិជ្ជារួចរាល់។", "success")
                return redirect(url_for("subjects.list_subjects"))
            except IntegrityError:
                db.session.rollback()
                flash("មុខវិជ្ជានេះមានរួចហើយ។", "danger")
        flash("សូមបញ្ចូលឈ្មោះមុខវិជ្ជា។", "danger")
    return render_template("subjects/list.html", subjects=Subject.query.order_by(Subject.name).all(), teachers=Teacher.query.order_by(Teacher.name).all())


@subjects_bp.route("/<int:subject_id>/update", methods=["POST"])
@login_required
@roles_required("admin")
def update_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    name = request.form.get("name", "").strip()
    if not name:
        flash("សូមបញ្ចូលឈ្មោះមុខវិជ្ជា។", "danger")
        return redirect(url_for("subjects.list_subjects"))
    subject.name = name
    subject.teacher_id = request.form.get("teacher_id") or None
    try:
        write_audit("update", "subject", subject.id, subject.name)
        db.session.commit()
        flash("បានកែប្រែមុខវិជ្ជារួចរាល់។", "success")
    except IntegrityError:
        db.session.rollback()
        flash("មុខវិជ្ជានេះមានរួចហើយ។", "danger")
    return redirect(url_for("subjects.list_subjects"))


@subjects_bp.route("/<int:subject_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    write_audit("delete", "subject", subject.id, subject.name)
    db.session.delete(subject)
    db.session.commit()
    flash("បានលុបមុខវិជ្ជារួចរាល់។", "success")
    return redirect(url_for("subjects.list_subjects"))
