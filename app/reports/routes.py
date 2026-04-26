from io import BytesIO

from flask import Blueprint, Response, render_template
from flask_login import login_required
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=letter)
    y = 750
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, "Student Report Cards")
    y -= 30
    pdf.setFont("Helvetica", 10)
    for student in Student.query.order_by(Student.name):
        pdf.drawString(40, y, f"{student.student_code} | {student.name} | {student.class_room or 'No class'} | Average: {student.average_score or 'N/A'}")
        y -= 18
        for score in student.scores:
            pdf.drawString(60, y, f"{score.subject.name}: {score.score}")
            y -= 14
        y -= 8
        if y < 80:
            pdf.showPage()
            y = 750
            pdf.setFont("Helvetica", 10)
    pdf.save()
    output.seek(0)
    return Response(output, mimetype="application/pdf", headers={"Content-Disposition": "attachment; filename=students.pdf"})
