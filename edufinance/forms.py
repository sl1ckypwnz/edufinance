from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import DecimalField, EmailField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    full_name = StringField("ФИО", validators=[DataRequired(), Length(min=2, max=120)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=8, max=128)])
    password_repeat = PasswordField("Повтор пароля", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Зарегистрироваться")


class AccountForm(FlaskForm):
    name = StringField("Название счета", validators=[DataRequired(), Length(max=100)])
    currency = SelectField("Валюта", choices=[("RUB", "RUB"), ("USD", "USD"), ("EUR", "EUR")])
    initial_balance = DecimalField(
        "Начальный баланс",
        default=Decimal("0.00"),
        places=2,
        validators=[DataRequired(), NumberRange(min=0, max=999999999)],
    )
    submit = SubmitField("Создать счет")


class TransactionForm(FlaskForm):
    account_id = SelectField("Счет", coerce=int, validators=[DataRequired()])
    operation_type = SelectField("Тип операции", choices=[("income", "Доход"), ("expense", "Расход")])
    category_id = SelectField("Категория", coerce=int, validators=[DataRequired()])
    amount = DecimalField("Сумма", places=2, validators=[DataRequired(), NumberRange(min=0.01, max=999999999)])
    comment = TextAreaField("Комментарий", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Добавить операцию")


class PaymentForm(FlaskForm):
    account_id = SelectField("Счет списания", coerce=int, validators=[DataRequired()])
    amount = DecimalField("Сумма платежа", places=2, validators=[DataRequired(), NumberRange(min=0.01, max=999999999)])
    recipient = StringField("Получатель", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Назначение платежа", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Смоделировать платеж")
