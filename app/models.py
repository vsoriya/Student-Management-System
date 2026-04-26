from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_teacher(self):
        return self.role == "teacher"


class ClassRoom(db.Model):
    __tablename__ = "class_rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher.id"))
    students = db.relationship("Student", back_populates="class_room", lazy=True)
    schedules = db.relationship("Schedule", back_populates="class_room", cascade="all, delete-orphan")

    def __repr__(self):
        return f"{self.grade} - {self.name}"


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String(50), nullable=False, unique=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(40))
    address = db.Column(db.String(255))
    guardian_name = db.Column(db.String(120))
    guardian_phone = db.Column(db.String(40))
    emergency_phone = db.Column(db.String(40))
    photo_url = db.Column(db.String(255))
    class_id = db.Column(db.Integer, db.ForeignKey("class_rooms.id"))

    class_room = db.relationship("ClassRoom", back_populates="students")
    scores = db.relationship("Score", back_populates="student", cascade="all, delete-orphan")
    attendances = db.relationship("Attendance", back_populates="student", cascade="all, delete-orphan")

    @property
    def average_score(self):
        if not self.scores:
            return None
        return round(sum(score.score for score in self.scores) / len(self.scores), 2)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher.id"))
    scores = db.relationship("Score", back_populates="subject", cascade="all, delete-orphan")
    schedules = db.relationship("Schedule", back_populates="subject", cascade="all, delete-orphan")


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True)
    phone = db.Column(db.String(40))
    specialty = db.Column(db.String(120))

    classes = db.relationship("ClassRoom", backref="teacher", lazy=True)
    subjects = db.relationship("Subject", backref="teacher", lazy=True)
    schedules = db.relationship("Schedule", back_populates="teacher", cascade="all, delete-orphan")


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    quiz_score = db.Column(db.Float, nullable=False, default=0)
    homework_score = db.Column(db.Float, nullable=False, default=0)
    midterm_score = db.Column(db.Float, nullable=False, default=0)
    final_score = db.Column(db.Float, nullable=False, default=0)
    score = db.Column(db.Float, nullable=False, default=0)

    student = db.relationship("Student", back_populates="scores")
    subject = db.relationship("Subject", back_populates="scores")
    __table_args__ = (db.UniqueConstraint("student_id", "subject_id", name="uq_student_subject"),)

    def calculate_total(self):
        self.score = round((self.quiz_score or 0) + (self.homework_score or 0) + (self.midterm_score or 0) + (self.final_score or 0), 2)
        return self.score

    @property
    def grade(self):
        if self.score >= 90:
            return "A"
        if self.score >= 80:
            return "B"
        if self.score >= 70:
            return "C"
        if self.score >= 60:
            return "D"
        return "F"


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default="Present")

    student = db.relationship("Student", back_populates="attendances")
    __table_args__ = (db.UniqueConstraint("student_id", "date", name="uq_student_attendance_date"),)


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(30), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("class_rooms.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher.id"))

    class_room = db.relationship("ClassRoom", back_populates="schedules")
    subject = db.relationship("Subject", back_populates="schedules")
    teacher = db.relationship("Teacher", back_populates="schedules")


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(db.String(80), nullable=False)
    entity = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer)
    message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref="audit_logs")
