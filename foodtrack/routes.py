from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    make_response,
)
from flask_login import login_user, current_user, logout_user, login_required
from . import db, bcrypt
from .models import User, Meal
from .forms import RegisterForm, LoginForm, MealForm
from datetime import date, timedelta, datetime, timezone
from sqlalchemy import func, extract
import csv
from io import StringIO

main = Blueprint("main", __name__)


@main.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.login"))


@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_pw
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created! You can now log in.", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("main.dashboard"))
            else:
                flash("Wrong Password, try again", "warning")
        else:
            flash("Email not registered", "danger")
    return render_template("login.html", form=form)


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("main.login"))


@main.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    week_mode = request.args.get("week", "0") == "1"
    selected_date_str = request.args.get("date")
    today = date.today()

    if week_mode:
        # --- WEEKLY VIEW ---
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)  # Sunday

        meals = (
            Meal.query.filter(Meal.user_id == current_user.id)
            .filter(Meal.date >= start_of_week)
            .filter(Meal.date <= end_of_week)
            .order_by(Meal.date)
            .all()
        )

        # totals per day for summary
        totals_by_day = (
            db.session.query(Meal.date, func.sum(Meal.cost))
            .filter(Meal.user_id == current_user.id)
            .filter(Meal.date >= start_of_week)
            .filter(Meal.date <= end_of_week)
            .group_by(Meal.date)
            .order_by(Meal.date)
            .all()
        )
        total_spent = sum(float(t[1]) for t in totals_by_day)

        return render_template(
            "dashboard.html",
            meals=meals,
            week_mode=True,
            start_of_week=start_of_week,
            end_of_week=end_of_week,
            totals_by_day=totals_by_day,
            total_spent=total_spent,
            now=lambda: datetime.now(timezone.utc),
        )

    # --- DAILY VIEW ---
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    meals = Meal.query.filter_by(user_id=current_user.id, date=selected_date).all()
    total = sum(meal.cost for meal in meals)

    # reminder only for today
    logged_meals = [m.meal_type.lower() for m in meals]
    all_meals = ["breakfast", "lunch", "supper"]
    missing_meals = (
        [m for m in all_meals if m not in logged_meals]
        if selected_date == today
        else []
    )

    return render_template(
        "dashboard.html",
        meals=meals,
        total=total,
        selected_date=selected_date,
        missing_meals=missing_meals,
        week_mode=False,
        now=lambda: datetime.now(timezone.utc),
    )


# add a meal
@main.route("/add", methods=["GET", "POST"])
def add_meal():
    form = MealForm()
    if form.validate_on_submit():
        meal = Meal(
            meal_type=form.meal_type.data,
            description=form.description.data,
            cost=form.cost.data,
            user_id=current_user.id,
        )
        existing_meal = Meal.query.filter_by(
            user_id=current_user.id,
            date=date.today(),
            meal_type=meal.meal_type,
        ).first()
        if existing_meal:
            flash(f"You have already logged {meal.meal_type} for today.", "warning")
            return redirect(url_for("main.dashboard"))
        db.session.add(meal)
        db.session.commit()
        flash("Meal added successfully!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_meal.html", form=form)


# edit a meal
@main.route("/edit/<int:meal_id>", methods=["GET", "POST"])
@login_required
def edit_meal(meal_id: int):
    meal = Meal.query.get_or_404(meal_id)
    if meal.owner != current_user:
        flash("You are not authorized to edit this meal.", "danger")
        return redirect(url_for("main.dashboard"))

    # prevent editing past meals
    if meal.date != date.today():
        flash("You cannot edit past meals.", "warning")
        return redirect(url_for("main.dashboard"))

    form = MealForm(obj=meal)
    if form.validate_on_submit():
        meal.meal_type = form.meal_type.data
        meal.description = form.description.data
        meal.cost = form.cost.data
        db.session.commit()
        flash("Meal updated successfully!", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("add_meal.html", form=form, edit=True)


# delete a meal
@main.route("/delete/<int:meal_id>", methods=["POST"])
@login_required
def delete_meal(meal_id: int):
    meal = Meal.query.get_or_404(meal_id)
    if meal.owner != current_user:
        flash("You are not authorized to delete this meal.", "danger")
        return redirect(url_for("main.dashboard"))

    # prevent deleting past meals
    if meal.date != date.today():
        flash("You cannot delete past meals.", "warning")
        return redirect(url_for("main.dashboard"))

    db.session.delete(meal)
    db.session.commit()
    flash("Meal deleted successfully!", "success")
    return redirect(url_for("main.dashboard"))


# reports
@main.route("/reports")
@login_required
def reports():
    view = request.args.get("view", "week")  # week or month
    today = date.today()

    if view == "month":
        meals = (
            Meal.query.filter(Meal.user_id == current_user.id)
            .filter(extract("year", Meal.date) == today.year)
            .filter(extract("month", Meal.date) == today.month)
            .all()
        )
    else:  # default current week
        start_of_week = date.fromisocalendar(
            today.isocalendar()[0], today.isocalendar()[1], 1
        )
        end_of_week = start_of_week + timedelta(days=6)
        meals = (
            Meal.query.filter(Meal.user_id == current_user.id)
            .filter(Meal.date >= start_of_week)
            .filter(Meal.date <= end_of_week)
            .all()
        )

        # aggregate for charts
    totals_by_day = (
        db.session.query(Meal.date, func.sum(Meal.cost))
        .filter(Meal.user_id == current_user.id)
        .group_by(Meal.date)
        .order_by(Meal.date)
        .all()
    )

    labels = [m[0].strftime("%b %d") for m in totals_by_day]
    values = [float(m[1]) for m in totals_by_day]

    if values:
        max_value = max(values)
        min_value = min(values)
        max_day = labels[values.index(max_value)]
        min_day = labels[values.index(min_value)]
    else:
        max_value = min_value = 0
        max_day = min_day = None

    total_spent = sum(values)
    avg_spent = round(total_spent / len(values), 2) if values else 0

    return render_template(
        "reports.html",
        view=view,
        meals=meals,
        labels=labels,
        values=values,
        total_spent=total_spent,
        avg_spent=avg_spent,
        max_day=max_day,
        min_day=min_day,
        max_value=max_value,
        min_value=min_value,
        totals_by_day=totals_by_day,
    )


# export meals as CSV
@main.route("/export_csv")
@login_required
def export_csv():
    meals = (
        Meal.query.filter_by(user_id=current_user.id).order_by(Meal.date.desc()).all()
    )

    # create a CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Date", "Meal Type", "Description", "Cost"])
    for meal in meals:
        writer.writerow(
            [
                meal.date.strftime("%Y-%m-%d"),
                meal.meal_type,
                meal.description,
                meal.cost,
            ]
        )

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = (
        f"attachment; filename=foodtrack_{current_user.username}_meals.csv"
    )
    output.headers["Content-type"] = "text/csv"
    return output
