import os
import shutil
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, request, url_for
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
    from .payments.routes import payments_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(classes_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(teachers_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payments_bp)

    from .models import AcademicTerm, Attendance, ClassRoom, FeePlan, Payment, Score, Student, Subject, Teacher, User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route("/")
    def index():
        return redirect(url_for("students.dashboard"))

    @app.route("/healthz")
    def healthz():
        try:
            db.session.execute(db.text("SELECT 1"))
            database = "ok"
        except Exception as exc:
            database = f"error: {exc.__class__.__name__}"
        return jsonify(
            {
                "app": "ok",
                "database": database,
                "database_configured": bool(os.getenv("DATABASE_URL")),
            }
        )

    @app.route("/deployment/init")
    def deployment_init():
        token = os.getenv("DEPLOY_SETUP_TOKEN")
        if not token or request.args.get("token") != token:
            return jsonify({"error": "invalid setup token"}), 403

        db.create_all()
        email = os.getenv("ADMIN_EMAIL", "vseyhaksoriya@gmail.com").strip().lower()
        password = os.getenv("ADMIN_PASSWORD", "Soriya@12345")
        admin = User.query.filter_by(email=email).first() or User(role="admin")
        admin.name = os.getenv("ADMIN_NAME", "Admin")
        admin.email = email
        admin.role = "admin"
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        return jsonify({"status": "initialized", "admin_email": admin.email})

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
