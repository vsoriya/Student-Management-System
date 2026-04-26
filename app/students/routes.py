from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.models import Attendance, ClassRoom, Score, Student, Subject
from app.utils import roles_required, write_audit
from .forms import student_payload, validate_student

students_bp = Blueprint("students", __name__, url_prefix="/students")


@students_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        student_count=Student.query.count(),
        class_count=ClassRoom.query.count(),
        subject_count=Subject.query.count(),
        attendance_count=Attendance.query.count(),
        recent_students=Student.query.order_by(Student.id.desc()).limit(5).all(),
        present_count=Attendance.query.filter_by(status="Present").count(),
        absent_count=Attendance.query.filter_by(status="Absent").count(),
    )


@students_bp.route("/")
@login_required
def list_students():
    if current_user.role == "student":
        own_student = Student.query.filter(
            or_(
                Student.student_code == current_user.email.split("@")[0],
                Student.name == current_user.name,
                Student.phone == current_user.email,
            )
        ).first()
        if own_student:
            return redirect(url_for("students.profile", student_id=own_student.id))
        flash("គណនីសិស្សនេះមិនទាន់ភ្ជាប់ជាមួយប្រវត្តិរូបសិស្សទេ។ សូមទាក់ទងអ្នកគ្រប់គ្រង។", "warning")
        return render_template("students/list.html", students=None, classes=[], search="", class_id=None)
    search = request.args.get("search", "").strip()
    class_id = request.args.get("class_id", type=int)
    page = request.args.get("page", 1, type=int)
    query = Student.query
    if search:
        query = query.filter(or_(Student.name.ilike(f"%{search}%"), Student.student_code.ilike(f"%{search}%")))
    if class_id:
        query = query.filter_by(class_id=class_id)
    students = query.order_by(Student.id.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template("students/list.html", students=students, classes=ClassRoom.query.all(), search=search, class_id=class_id)


@students_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin", "teacher")
def create_student():
    if request.method == "POST":
        data = student_payload(request.form)
        errors = validate_student(data)
        if Student.query.filter_by(student_code=data["student_code"]).first():
            errors.append("លេខកូដសិស្សនេះមានរួចហើយ។")
        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            student = Student(**data)
            db.session.add(student)
            db.session.flush()
            write_audit("create", "student", student.id, student.name)
            db.session.commit()
            flash("បានបង្កើតសិស្សរួចរាល់។", "success")
            return redirect(url_for("students.list_students"))
    return render_template("students/create.html", classes=ClassRoom.query.all())


@students_bp.route("/<int:student_id>")
@login_required
def profile(student_id):
    student = Student.query.get_or_404(student_id)
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template("students/profile.html", student=student, subjects=subjects)


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "teacher")
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == "POST":
        data = student_payload(request.form)
        errors = validate_student(data)
        existing = Student.query.filter(Student.student_code == data["student_code"], Student.id != student.id).first()
        if existing:
            errors.append("លេខកូដសិស្សនេះមានរួចហើយ។")
        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            for key, value in data.items():
                setattr(student, key, value)
            write_audit("update", "student", student.id, student.name)
            db.session.commit()
            flash("បានកែប្រែសិស្សរួចរាល់។", "success")
            return redirect(url_for("students.profile", student_id=student.id))
    return render_template("students/edit.html", student=student, classes=ClassRoom.query.all())


@students_bp.route("/<int:student_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    write_audit("delete", "student", student.id, student.name)
    db.session.delete(student)
    db.session.commit()
    flash("បានលុបសិស្សរួចរាល់។", "success")
    return redirect(url_for("students.list_students"))


@students_bp.route("/<int:student_id>/scores", methods=["POST"])
@login_required
@roles_required("admin", "teacher")
def save_score(student_id):
    Student.query.get_or_404(student_id)
    subject_id = request.form.get("subject_id", type=int)
    quiz = request.form.get("quiz_score", type=float) or 0
    homework = request.form.get("homework_score", type=float) or 0
    midterm = request.form.get("midterm_score", type=float) or 0
    final = request.form.get("final_score", type=float) or 0
    score_value = quiz + homework + midterm + final
    if subject_id and 0 <= score_value <= 100:
        score = Score.query.filter_by(student_id=student_id, subject_id=subject_id).first()
        if score:
            score.quiz_score = quiz
            score.homework_score = homework
            score.midterm_score = midterm
            score.final_score = final
            score.calculate_total()
        else:
            score = Score(student_id=student_id, subject_id=subject_id, quiz_score=quiz, homework_score=homework, midterm_score=midterm, final_score=final)
            score.calculate_total()
            db.session.add(score)
        write_audit("score", "student", student_id, f"subject={subject_id}, total={score.score}")
        db.session.commit()
        flash("បានរក្សាទុកពិន្ទុរួចរាល់។", "success")
    else:
        flash("ពិន្ទុត្រូវនៅចន្លោះ ០ ដល់ ១០០។", "danger")
    return redirect(url_for("students.profile", student_id=student_id))
