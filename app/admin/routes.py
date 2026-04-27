from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import AuditLog, ClassRoom, Enrollment, Schedule, Subject, Teacher
from app.utils import roles_required, write_audit

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/enrollments")
@login_required
@roles_required("admin")
def enrollments():
    return render_template(
        "admin/enrollments.html",
        enrollments=Enrollment.query.order_by(Enrollment.enrolled_at.desc()).all(),
        classes=ClassRoom.query.order_by(ClassRoom.grade, ClassRoom.name).all(),
    )


@admin_bp.route("/enrollments/<int:enrollment_id>/approve", methods=["POST"])
@login_required
@roles_required("admin")
def approve_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    class_id = request.form.get("class_id", type=int)
    if not class_id:
        flash("សូមជ្រើសរើសថ្នាក់មុន approve។", "danger")
        return redirect(url_for("admin.enrollments"))
    class_room = ClassRoom.query.get_or_404(class_id)
    enrollment.class_id = class_room.id
    enrollment.status = "Active"
    enrollment.student.class_id = class_room.id
    from datetime import datetime
    enrollment.approved_at = datetime.utcnow()
    write_audit("approve", "enrollment", enrollment.id, enrollment.student.name)
    db.session.commit()
    flash("បាន approve ការចុះឈ្មោះ និង assign ថ្នាក់រួចរាល់។", "success")
    return redirect(url_for("admin.enrollments"))


@admin_bp.route("/enrollments/<int:enrollment_id>/reject", methods=["POST"])
@login_required
@roles_required("admin")
def reject_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    enrollment.status = "Rejected"
    enrollment.class_id = None
    enrollment.student.class_id = None
    write_audit("reject", "enrollment", enrollment.id, enrollment.student.name)
    db.session.commit()
    flash("បាន reject ការចុះឈ្មោះរួចរាល់។", "success")
    return redirect(url_for("admin.enrollments"))


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
