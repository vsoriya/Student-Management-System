from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import AcademicTerm, AuditLog, ClassRoom, Enrollment, Schedule, Subject, Teacher
from app.utils import active_term, roles_required, write_audit

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value)


@admin_bp.route("/terms", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def terms():
    if request.method == "POST":
        term = AcademicTerm(
            name=request.form.get("name", "").strip(),
            academic_year=request.form.get("academic_year", "").strip(),
            semester=request.form.get("semester", "").strip(),
            start_date=parse_date(request.form.get("start_date")),
            end_date=parse_date(request.form.get("end_date")),
            is_active=bool(request.form.get("is_active")),
        )
        if not term.name or not term.academic_year or not term.semester:
            flash("សូមបញ្ចូលឈ្មោះ term, ឆ្នាំសិក្សា និង semester។", "danger")
        else:
            if term.is_active:
                AcademicTerm.query.update({"is_active": False})
            db.session.add(term)
            db.session.flush()
            write_audit("create", "academic_term", term.id, str(term))
            db.session.commit()
            flash("បានបង្កើត academic term រួចរាល់។", "success")
            return redirect(url_for("admin.terms"))
    return render_template("admin/terms.html", terms=AcademicTerm.query.order_by(AcademicTerm.id.desc()).all())


@admin_bp.route("/terms/<int:term_id>/activate", methods=["POST"])
@login_required
@roles_required("admin")
def activate_term(term_id):
    term = AcademicTerm.query.get_or_404(term_id)
    AcademicTerm.query.update({"is_active": False})
    term.is_active = True
    write_audit("activate", "academic_term", term.id, str(term))
    db.session.commit()
    flash("បានកំណត់ active term រួចរាល់។", "success")
    return redirect(url_for("admin.terms"))


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
    if not enrollment.term_id:
        enrollment.term = active_term()
    enrollment.status = "Active"
    enrollment.student.class_id = class_room.id
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
            term_id=request.form.get("term_id") or None,
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
        terms=AcademicTerm.query.order_by(AcademicTerm.id.desc()).all(),
        active_term=active_term(),
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
