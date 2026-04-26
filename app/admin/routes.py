from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import AuditLog, ClassRoom, Schedule, Subject, Teacher
from app.utils import roles_required, write_audit

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/schedule", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def schedule():
    if request.method == "POST":
        item = Schedule(
            day=request.form.get("day", "").strip(),
            start_time=request.form.get("start_time", "").strip(),
            end_time=request.form.get("end_time", "").strip(),
            class_id=request.form.get("class_id"),
            subject_id=request.form.get("subject_id"),
            teacher_id=request.form.get("teacher_id") or None,
        )
        db.session.add(item)
        db.session.flush()
        write_audit("create", "schedule", item.id, item.day)
        db.session.commit()
        flash("បានបង្កើតកាលវិភាគរួចរាល់។", "success")
        return redirect(url_for("admin.schedule"))
    return render_template(
        "admin/schedule.html",
        schedules=Schedule.query.order_by(Schedule.day, Schedule.start_time).all(),
        classes=ClassRoom.query.order_by(ClassRoom.grade, ClassRoom.name).all(),
        subjects=Subject.query.order_by(Subject.name).all(),
        teachers=Teacher.query.order_by(Teacher.name).all(),
    )


@admin_bp.route("/schedule/<int:schedule_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_schedule(schedule_id):
    item = Schedule.query.get_or_404(schedule_id)
    write_audit("delete", "schedule", item.id, item.day)
    db.session.delete(item)
    db.session.commit()
    flash("បានលុបកាលវិភាគរួចរាល់។", "success")
    return redirect(url_for("admin.schedule"))


@admin_bp.route("/audit")
@login_required
@roles_required("admin")
def audit_log():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return render_template("admin/audit.html", logs=logs)
