from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from edufinance.forms import LoginForm, RegisterForm
from edufinance.models import Role, User, db
from edufinance.security import log_action


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash("Пользователь с таким email уже существует.", "error")
            return render_template("register.html", form=form)

        role = Role.query.filter_by(name="user").first()
        user = User(email=form.email.data.lower(), full_name=form.full_name.data.strip(), role=role)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        log_action(user.id, "user_registered", "New user registration")
        flash("Регистрация выполнена. Теперь можно войти.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            log_action(user.id, "user_login", "Successful login")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        flash("Неверный email или пароль.", "error")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        log_action(current_user.id, "user_logout", "User logged out")
    logout_user()
    return redirect(url_for("auth.login"))
