from io import BytesIO

from flask import Blueprint, Response, render_template
from flask_login import login_required
from openpyxl import Workbook

from app.models import Student

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def report_cards():
    return render_template("reports/cards.html", students=Student.query.order_by(Student.name).all())


@reports_bp.route("/students.xlsx")
@login_required
def export_excel():
    wb = Workbook()
    ws = wb.active
    ws.title = "សិស្ស"
    ws.append(["លេខកូដ", "ឈ្មោះ", "ភេទ", "អាយុ", "ទូរស័ព្ទ", "ថ្នាក់", "មធ្យមភាគ"])
    for student in Student.query.order_by(Student.name):
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
    students = Student.query.order_by(Student.name).all()
    return render_template("reports/print.html", students=students)
