import shutil
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, url_for
from dotenv import load_dotenv

from config import Config
from .extensions import db, login_manager, migrate


def create_app(config_class=Config):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    app.config.from_pyfile("config.py", silent=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .auth.routes import auth_bp
    from .students.routes import students_bp
    from .classes.routes import classes_bp
    from .subjects.routes import subjects_bp
    from .attendance.routes import attendance_bp
    from .reports.routes import reports_bp
    from .teachers.routes import teachers_bp
    from .admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(classes_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(teachers_bp)
    app.register_blueprint(admin_bp)

    from .models import Attendance, ClassRoom, Score, Student, Subject, Teacher, User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route("/")
    def index():
        return redirect(url_for("students.dashboard"))

    @app.template_filter("km_role")
    def km_role(value):
        return {"admin": "អ្នកគ្រប់គ្រង", "teacher": "គ្រូបង្រៀន", "student": "សិស្ស"}.get(value, value)

    @app.template_filter("km_status")
    def km_status(value):
        return {"Present": "មានវត្តមាន", "Absent": "អវត្តមាន", "Late": "យឺត", "Excused": "មានច្បាប់"}.get(value, value)

    @app.template_filter("km_gender")
    def km_gender(value):
        return {"Male": "ប្រុស", "Female": "ស្រី", "Other": "ផ្សេងៗ"}.get(value, value)

    @app.template_filter("grade_color")
    def grade_color(value):
        return {"A": "grade-a", "B": "grade-b", "C": "grade-c", "D": "grade-d", "F": "grade-f"}.get(value, "")

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Database tables created.")

    @app.cli.command("create-admin")
    def create_admin():
        if User.query.filter_by(email="admin@example.com").first():
            print("Admin already exists.")
            return
        user = User(name="Admin", email="admin@example.com", role="admin")
        user.set_password("admin123")
        db.session.add(user)
        db.session.commit()
        print("Admin created: admin@example.com / admin123")

    @app.cli.command("backup-db")
    def backup_db():
        uri = app.config["SQLALCHEMY_DATABASE_URI"]
        backup_dir = Path(app.config["BACKUP_DIR"])
        backup_dir.mkdir(exist_ok=True)
        if not uri.startswith("sqlite:///"):
            print("Use mysqldump for MySQL backups. Example: mysqldump -u root -p student_management > backups/backup.sql")
            return
        source = Path(uri.replace("sqlite:///", ""))
        target = backup_dir / f"student_management_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(source, target)
        print(f"Backup created: {target}")

    return app
