from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from .models import Meal


class RegisterForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=50)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=80)]
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class MealForm(FlaskForm):
    meal_type = SelectField(
        "Meal Type",
        choices=[
            ("Breakfast", "Breakfast"),
            ("Lunch", "Lunch"),
            ("Supper", "Supper"),
            ("Snack", "Snack"),
        ],
    )
    description = StringField("Description", validators=[DataRequired()])
    cost = FloatField("Cost (Ksh)", validators=[DataRequired()])
    submit = SubmitField("Add Meal")
