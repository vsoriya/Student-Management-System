from flask import abort, Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.models import Attendance, ClassRoom, Enrollment, Score, Schedule, Student, Subject
from app.utils import active_term, current_student_profile, current_teacher_profile, roles_required, teacher_can_access_student, teacher_class_ids, teacher_subject_ids, write_audit
from .forms import student_payload, validate_student

students_bp = Blueprint("students", __name__, url_prefix="/students")


@students_bp.route("/dashboard")
@login_required
def dashboard():
    own_student = None
    student_schedules = []
    if current_user.role == "student":
        own_student = current_student_profile()
        if own_student and own_student.class_id:
            schedule_query = Schedule.query.filter_by(class_id=own_student.class_id)
            term = active_term()
            if term:
                schedule_query = schedule_query.filter((Schedule.term_id == term.id) | (Schedule.term_id.is_(None)))
            student_schedules = schedule_query.order_by(Schedule.day, Schedule.start_time).all()
    student_count = Student.query.count()
    recent_students = Student.query.order_by(Student.id.desc()).limit(5).all()
    if current_user.role == "student":
        student_count = 1 if own_student else 0
        recent_students = [own_student] if own_student else []
        class_count = 1 if own_student and own_student.class_id else 0
        subject_count = len({item.subject_id for item in student_schedules})
        attendance_count = Attendance.query.filter_by(student_id=own_student.id).count() if own_student else 0
        present_count = Attendance.query.filter_by(student_id=own_student.id, status="Present").count() if own_student else 0
        absent_count = Attendance.query.filter_by(student_id=own_student.id, status="Absent").count() if own_student else 0
    else:
        class_count = ClassRoom.query.count()
        subject_count = Subject.query.count()
        attendance_count = Attendance.query.count()
        present_count = Attendance.query.filter_by(status="Present").count()
        absent_count = Attendance.query.filter_by(status="Absent").count()
        if current_user.role == "teacher":
            class_ids = teacher_class_ids()
            subject_ids = teacher_subject_ids()
            scoped_students = Student.query.filter(Student.class_id.in_(class_ids)).all() if class_ids else []
            student_ids = [student.id for student in scoped_students]
            student_count = len(scoped_students)
            class_count = len(class_ids)
            subject_count = len(subject_ids)
            attendance_count = Attendance.query.filter(Attendance.student_id.in_(student_ids)).count() if student_ids else 0
            present_count = Attendance.query.filter(Attendance.student_id.in_(student_ids), Attendance.status == "Present").count() if student_ids else 0
            absent_count = Attendance.query.filter(Attendance.student_id.in_(student_ids), Attendance.status == "Absent").count() if student_ids else 0
            recent_students = sorted(scoped_students, key=lambda student: student.id, reverse=True)[:5]
    return render_template(
        "dashboard.html",
        student_count=student_count,
        class_count=class_count,
        subject_count=subject_count,
        attendance_count=attendance_count,
        recent_students=recent_students,
        present_count=present_count,
        absent_count=absent_count,
        pending_enrollment_count=Enrollment.query.filter_by(status="Pending").count(),
        own_student=own_student,
        student_schedules=student_schedules,
    )


@students_bp.route("/")
@login_required
def list_students():
    if current_user.role == "student":
        own_student = current_student_profile()
        if own_student:
            return redirect(url_for("students.profile", student_id=own_student.id))
        flash("គណនីសិស្សនេះមិនទាន់ភ្ជាប់ជាមួយប្រវត្តិរូបសិស្សទេ។ សូមទាក់ទងអ្នកគ្រប់គ្រង។", "warning")
        return render_template("students/list.html", students=None, classes=[], search="", class_id=None)
    search = request.args.get("search", "").strip()
    class_id = request.args.get("class_id", type=int)
    page = request.args.get("page", 1, type=int)
    query = Student.query
    teacher_classes = None
    if current_user.role == "teacher":
        teacher_classes = teacher_class_ids()
        query = query.filter(Student.class_id.in_(teacher_classes)) if teacher_classes else query.filter(False)
    if search:
        query = query.filter(or_(Student.name.ilike(f"%{search}%"), Student.student_code.ilike(f"%{search}%")))
    if class_id:
        if current_user.role == "teacher" and class_id not in teacher_classes:
            abort(403)
        query = query.filter_by(class_id=class_id)
    students = query.order_by(Student.id.desc()).paginate(page=page, per_page=10, error_out=False)
    classes = ClassRoom.query.all()
    if current_user.role == "teacher":
        classes = ClassRoom.query.filter(ClassRoom.id.in_(teacher_classes)).all() if teacher_classes else []
    return render_template("students/list.html", students=students, classes=classes, search=search, class_id=class_id)


@students_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def create_student():
    classes = ClassRoom.query.all()
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
    return render_template("students/create.html", classes=classes)


@students_bp.route("/<int:student_id>")
@login_required
def profile(student_id):
    student = Student.query.get_or_404(student_id)
    if current_user.role == "student":
        own_student = current_student_profile()
        if not own_student or own_student.id != student.id:
            abort(403)
    if current_user.role == "teacher" and not teacher_can_access_student(student):
        abort(403)
    subjects = Subject.query.order_by(Subject.name).all()
    if current_user.role == "teacher":
        subject_ids = teacher_subject_ids()
        subjects = Subject.query.filter(Subject.id.in_(subject_ids)).order_by(Subject.name).all() if subject_ids else []
    return render_template("students/profile.html", student=student, subjects=subjects)


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    classes = ClassRoom.query.all()
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
    return render_template("students/edit.html", student=student, classes=classes)


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
    student = Student.query.get_or_404(student_id)
    subject_id = request.form.get("subject_id", type=int)
    if current_user.role == "teacher":
        if not teacher_can_access_student(student) or subject_id not in teacher_subject_ids():
            abort(403)
    quiz = request.form.get("quiz_score", type=float) or 0
    homework = request.form.get("homework_score", type=float) or 0
    midterm = request.form.get("midterm_score", type=float) or 0
    final = request.form.get("final_score", type=float) or 0
    score_value = quiz + homework + midterm + final
    if subject_id and 0 <= score_value <= 100:
        term = active_term()
        score_query = Score.query.filter_by(student_id=student_id, subject_id=subject_id)
        if term:
            score_query = score_query.filter((Score.term_id == term.id) | (Score.term_id.is_(None)))
        score = score_query.first()
        if score:
            score.quiz_score = quiz
            score.homework_score = homework
            score.midterm_score = midterm
            score.final_score = final
            score.calculate_total()
        else:
            score = Score(student_id=student_id, subject_id=subject_id, term=term, quiz_score=quiz, homework_score=homework, midterm_score=midterm, final_score=final)
            score.calculate_total()
            db.session.add(score)
        write_audit("score", "student", student_id, f"subject={subject_id}, total={score.score}")
        db.session.commit()
        flash("បានរក្សាទុកពិន្ទុរួចរាល់។", "success")
    else:
        flash("ពិន្ទុត្រូវនៅចន្លោះ ០ ដល់ ១០០។", "danger")
    return redirect(url_for("students.profile", student_id=student_id))
