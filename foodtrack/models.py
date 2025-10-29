from foodtrack import db, login_manager
from flask_login import UserMixin
from datetime import date

# make a unique meal_type per user for each day
from sqlalchemy import UniqueConstraint


@login_manager.user_loader
def load_user(user_id):
    from foodtrack.models import User

    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    meals = db.relationship("Meal", backref="owner", lazy=True)

    def __repr__(self):
        return f"{self.id,self.username,self.password}"


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    __table_args__ = (
        UniqueConstraint(
            "user_id", "date", "meal_type", name="unique_meal_per_user_per_day"
        ),
    )

    def __repr__(self):
        return (
            f"<Meal {self.meal_type} - {self.description} on {self.date}- {self.cost}>"
        )
