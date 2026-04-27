from io import BytesIO

from flask import Blueprint, Response, render_template
from flask_login import current_user, login_required
from openpyxl import Workbook

from app.models import Student
from app.utils import current_student_profile, teacher_class_ids

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def visible_students():
    if current_user.role == "student":
        student = current_student_profile()
        return [student] if student else []
    if current_user.role == "teacher":
        class_ids = teacher_class_ids()
        return Student.query.filter(Student.class_id.in_(class_ids)).order_by(Student.name).all() if class_ids else []
    return Student.query.order_by(Student.name).all()


@reports_bp.route("/")
@login_required
def report_cards():
    return render_template("reports/cards.html", students=visible_students())


@reports_bp.route("/students.xlsx")
@login_required
def export_excel():
    wb = Workbook()
    ws = wb.active
    ws.title = "សិស្ស"
    ws.append(["លេខកូដ", "ឈ្មោះ", "ភេទ", "អាយុ", "ទូរស័ព្ទ", "ថ្នាក់", "មធ្យមភាគ"])
    for student in visible_students():
        ws.append([
            student.student_code,
            student.name,
            student.gender,
            student.age,
            student.phone,
            str(student.class_room or ""),
            student.average_score or "",
        ])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=students.xlsx"})


@reports_bp.route("/students.pdf")
@login_required
def export_pdf():
    return render_template("reports/print.html", students=visible_students())
