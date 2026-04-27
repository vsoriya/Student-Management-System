from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Attendance, ClassRoom, Student
from app.utils import active_term, roles_required, teacher_class_ids, write_audit

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


@attendance_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required("admin", "teacher")
def attendance_sheet():
    selected_date = request.values.get("date") or date.today().isoformat()
    class_id = request.values.get("class_id", type=int)
    classes = ClassRoom.query.all()
    if current_user.role == "teacher":
        class_ids = teacher_class_ids()
        classes = ClassRoom.query.filter(ClassRoom.id.in_(class_ids)).all() if class_ids else []
        if class_id and class_id not in class_ids:
            flash("អ្នកអាចកត់វត្តមានបានតែក្នុងថ្នាក់ដែលអ្នកបង្រៀនប៉ុណ្ណោះ។", "danger")
            return redirect(url_for("attendance.attendance_sheet", date=selected_date))
    students_query = Student.query
    if current_user.role == "teacher":
        students_query = students_query.filter(Student.class_id.in_(class_ids)) if class_ids else students_query.filter(False)
    if class_id:
        students_query = students_query.filter_by(class_id=class_id)
    students = students_query.order_by(Student.name).all()

    if request.method == "POST":
        term = active_term()
        for student in students:
            status = request.form.get(f"status_{student.id}", "Absent")
            record = Attendance.query.filter_by(student_id=student.id, date=date.fromisoformat(selected_date)).first()
            if record:
                record.status = status
            else:
                db.session.add(Attendance(student_id=student.id, term=term, date=date.fromisoformat(selected_date), status=status))
        db.session.commit()
        write_audit("attendance", "attendance", None, selected_date)
        db.session.commit()
        flash("បានរក្សាទុកវត្តមានរួចរាល់។", "success")
        return redirect(url_for("attendance.attendance_sheet", date=selected_date, class_id=class_id or ""))

    records = {
        item.student_id: item.status
        for item in Attendance.query.filter_by(date=date.fromisoformat(selected_date)).all()
    }
    return render_template("attendance/sheet.html", students=students, classes=classes, selected_date=selected_date, class_id=class_id, records=records)
