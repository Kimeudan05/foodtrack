from flask import render_template, abort, make_response
from flask_login import login_required, current_user
from sqlalchemy import func
from foodtrack import db
from foodtrack.models import User, Meal
from . import admin_bp
import csv
from io import StringIO


# optional decorator to restrict access to admin users only
def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(current_user, "is_admin", False):
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_meals = Meal.query.count()
    total_spend = db.session.query(func.sum(Meal.cost)).scalar() or 0
    avg_cost = total_spend / total_meals if total_meals > 0 else 0

    # weekly spend trends
    totals_by_day = (
        db.session.query(Meal.date, func.sum(Meal.cost))
        .group_by(Meal.date)
        .order_by(Meal.date.desc())
        .limit(7)
        .all()
    )
    labels = [d.strftime("%b %d") for d, _ in totals_by_day]
    values = [float(total) for _, total in totals_by_day]

    users = (
        db.session.query(
            User.id,
            User.username,
            func.count(Meal.id).label("meal_count"),
            func.coalesce(func.sum(Meal.cost), 0).label("total_cost"),
        )
        .outerjoin(Meal)
        .group_by(User.id)
        .order_by(User.username)
        .all()
    )

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_meals=total_meals,
        total_spend=total_spend,
        avg_cost=avg_cost,
        labels=labels,
        values=values,
        users=users,
    )


@admin_bp.route("/admin/user/<int:user_id>")
@login_required
@admin_required
def user_detail(user_id):
    from datetime import date

    user = User.query.get_or_404(user_id)

    # Get all meals for this user
    meals = Meal.query.filter_by(user_id=user.id).order_by(Meal.date.desc()).all()

    total_spent = sum(m.cost for m in meals)
    total_meals = len(meals)

    # Daily spend trend
    from sqlalchemy import func

    totals_by_day = (
        db.session.query(Meal.date, func.sum(Meal.cost))
        .filter(Meal.user_id == user.id)
        .group_by(Meal.date)
        .order_by(Meal.date)
        .all()
    )
    labels = [d.strftime("%b %d") for d, _ in totals_by_day]
    values = [float(v) for _, v in totals_by_day]

    return render_template(
        "admin_user_detail.html",
        user=user,
        meals=meals,
        total_spent=total_spent,
        total_meals=total_meals,
        labels=labels,
        values=values,
        today=date.today(),
    )


# export user meals as CSV
@admin_bp.route("/admin/user/<int:user_id>/export")
@login_required
@admin_required
def export_user_meals(user_id):
    user = User.query.get_or_404(user_id)
    meals = Meal.query.filter_by(user_id=user.id).order_by(Meal.date.desc()).all()

    # create CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Date", "Meal" "Description", "Cost (Ksh)"])
    for meal in meals:
        writer.writerow(
            [
                meal.date.strftime("%Y-%m-%d"),
                meal.meal_type,
                meal.description,
                f"{meal.cost:.2f}",
            ]
        )

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = (
        f"attachment; filename={user.username}_meals.csv"
    )
    output.headers["Content-type"] = "text/csv"
    return output
