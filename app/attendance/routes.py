from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import Attendance, ClassRoom, Student
from app.utils import roles_required, write_audit

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


@attendance_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required("admin", "teacher")
def attendance_sheet():
    selected_date = request.values.get("date") or date.today().isoformat()
    class_id = request.values.get("class_id", type=int)
    students_query = Student.query
    if class_id:
        students_query = students_query.filter_by(class_id=class_id)
    students = students_query.order_by(Student.name).all()

    if request.method == "POST":
        for student in students:
            status = request.form.get(f"status_{student.id}", "Absent")
            record = Attendance.query.filter_by(student_id=student.id, date=date.fromisoformat(selected_date)).first()
            if record:
                record.status = status
            else:
                db.session.add(Attendance(student_id=student.id, date=date.fromisoformat(selected_date), status=status))
        db.session.commit()
        write_audit("attendance", "attendance", None, selected_date)
        db.session.commit()
        flash("បានរក្សាទុកវត្តមានរួចរាល់។", "success")
        return redirect(url_for("attendance.attendance_sheet", date=selected_date, class_id=class_id or ""))

    records = {
        item.student_id: item.status
        for item in Attendance.query.filter_by(date=date.fromisoformat(selected_date)).all()
    }
    return render_template("attendance/sheet.html", students=students, classes=ClassRoom.query.all(), selected_date=selected_date, class_id=class_id, records=records)
