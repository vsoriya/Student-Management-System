from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import AcademicTerm, ClassRoom, FeePlan, Payment, Student
from app.utils import active_term, current_student_profile, roles_required, write_audit

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


def parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value)


def plan_summary(plan):
    paid = sum(payment.amount for payment in plan.payments)
    student_count = Student.query.filter_by(class_id=plan.class_id).count()
    expected = plan.amount * student_count
    return {
        "paid": round(paid, 2),
        "expected": round(expected, 2),
        "balance": round(expected - paid, 2),
        "student_count": student_count,
    }


@payments_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def plans():
    if request.method == "POST":
        class_id = request.form.get("class_id", type=int)
        amount = request.form.get("amount", type=float)
        if not class_id or amount is None or amount < 0:
            flash("សូមជ្រើសថ្នាក់ និងបញ្ចូលតម្លៃសិក្សាឱ្យបានត្រឹមត្រូវ។", "danger")
        else:
            plan = FeePlan(
                class_id=class_id,
                term_id=request.form.get("term_id", type=int) or None,
                amount=amount,
                due_date=parse_date(request.form.get("due_date")),
                note=request.form.get("note", "").strip(),
            )
            db.session.add(plan)
            db.session.flush()
            write_audit("create", "fee_plan", plan.id, f"class={class_id}, amount={amount}")
            db.session.commit()
            flash("បានបង្កើត fee plan រួចរាល់។", "success")
            return redirect(url_for("payments.plans"))

    plans = FeePlan.query.order_by(FeePlan.id.desc()).all()
    return render_template(
        "payments/plans.html",
        plans=plans,
        summaries={plan.id: plan_summary(plan) for plan in plans},
        classes=ClassRoom.query.order_by(ClassRoom.grade, ClassRoom.name).all(),
        terms=AcademicTerm.query.order_by(AcademicTerm.id.desc()).all(),
        active_term=active_term(),
    )


@payments_bp.route("/<int:plan_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def plan_detail(plan_id):
    plan = FeePlan.query.get_or_404(plan_id)
    students = Student.query.filter_by(class_id=plan.class_id).order_by(Student.name).all()
    if request.method == "POST":
        student_id = request.form.get("student_id", type=int)
        amount = request.form.get("amount", type=float)
        if not student_id or amount is None or amount <= 0:
            flash("សូមជ្រើសសិស្ស និងបញ្ចូលចំនួនប្រាក់ឱ្យបានត្រឹមត្រូវ។", "danger")
        elif student_id not in {student.id for student in students}:
            abort(403)
        else:
            payment = Payment(
                student_id=student_id,
                fee_plan_id=plan.id,
                amount=amount,
                paid_at=parse_date(request.form.get("paid_at")) or date.today(),
                note=request.form.get("note", "").strip(),
            )
            db.session.add(payment)
            db.session.flush()
            write_audit("create", "payment", payment.id, f"student={student_id}, amount={amount}")
            db.session.commit()
            flash("បានរក្សាទុកការបង់ប្រាក់រួចរាល់។", "success")
            return redirect(url_for("payments.plan_detail", plan_id=plan.id))

    paid_by_student = {
        student.id: round(sum(payment.amount for payment in plan.payments if payment.student_id == student.id), 2)
        for student in students
    }
    return render_template(
        "payments/detail.html",
        plan=plan,
        students=students,
        paid_by_student=paid_by_student,
        today=date.today().isoformat(),
    )


@payments_bp.route("/mine")
@login_required
def my_payments():
    if current_user.role != "student":
        return redirect(url_for("payments.plans"))
    student = current_student_profile()
    plans = []
    paid_by_plan = {}
    if student and student.class_id:
        plans = FeePlan.query.filter_by(class_id=student.class_id).order_by(FeePlan.id.desc()).all()
        for plan in plans:
            paid_by_plan[plan.id] = round(sum(payment.amount for payment in plan.payments if payment.student_id == student.id), 2)
    return render_template("payments/mine.html", student=student, plans=plans, paid_by_plan=paid_by_plan)
