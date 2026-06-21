from collections import defaultdict
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from edufinance.forms import AccountForm, PaymentForm, TransactionForm
from edufinance.models import Account, Category, Payment, Transaction, db
from edufinance.security import log_action


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.created_at.desc()).all()
    transactions = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(8)
        .all()
    )
    total_balance = sum((account.balance for account in accounts), Decimal("0.00"))
    return render_template("dashboard.html", accounts=accounts, transactions=transactions, total_balance=total_balance)


@main_bp.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts():
    form = AccountForm()
    if form.validate_on_submit():
        account = Account(
            user_id=current_user.id,
            name=form.name.data.strip(),
            currency=form.currency.data,
            balance=form.initial_balance.data,
        )
        db.session.add(account)
        db.session.commit()
        log_action(current_user.id, "account_created", f"Account: {account.name}")
        flash("Счет создан.", "success")
        return redirect(url_for("main.accounts"))

    accounts_list = Account.query.filter_by(user_id=current_user.id).order_by(Account.created_at.desc()).all()
    return render_template("accounts.html", form=form, accounts=accounts_list)


@main_bp.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():
    form = TransactionForm()
    user_accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.name.asc()).all()
    categories = Category.query.order_by(Category.operation_type.asc(), Category.name.asc()).all()
    form.account_id.choices = [(account.id, f"{account.name} ({account.currency})") for account in user_accounts]
    form.category_id.choices = [(category.id, f"{category.name} / {category.operation_type}") for category in categories]

    if not user_accounts:
        flash("Сначала создайте финансовый счет.", "info")
        return redirect(url_for("main.accounts"))

    if form.validate_on_submit():
        account = Account.query.filter_by(id=form.account_id.data, user_id=current_user.id).first_or_404()
        amount = form.amount.data
        operation_type = form.operation_type.data

        if operation_type == "expense" and account.balance < amount:
            flash("Недостаточно средств для расходной операции.", "error")
            return redirect(url_for("main.transactions"))

        transaction = Transaction(
            user_id=current_user.id,
            account_id=account.id,
            category_id=form.category_id.data,
            operation_type=operation_type,
            amount=amount,
            comment=form.comment.data,
        )
        account.balance = account.balance + amount if operation_type == "income" else account.balance - amount
        db.session.add(transaction)
        db.session.commit()
        log_action(current_user.id, "transaction_created", f"{operation_type}: {amount}")
        flash("Операция добавлена.", "success")
        return redirect(url_for("main.transactions"))

    transaction_list = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template("transactions.html", form=form, transactions=transaction_list)


@main_bp.route("/payments", methods=["GET", "POST"])
@login_required
def payments():
    form = PaymentForm()
    user_accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.name.asc()).all()
    form.account_id.choices = [(account.id, f"{account.name} ({account.currency})") for account in user_accounts]

    if not user_accounts:
        flash("Для моделирования платежа сначала создайте счет.", "info")
        return redirect(url_for("main.accounts"))

    if form.validate_on_submit():
        account = Account.query.filter_by(id=form.account_id.data, user_id=current_user.id).first_or_404()
        amount = form.amount.data
        status = "confirmed" if account.balance >= amount else "declined"
        payment = Payment(
            user_id=current_user.id,
            account_id=account.id,
            amount=amount,
            recipient=form.recipient.data.strip(),
            description=form.description.data,
            status=status,
        )
        db.session.add(payment)

        if status == "confirmed":
            payment_category = Category.query.filter_by(name="Платежи", operation_type="expense").first()
            account.balance -= amount
            db.session.add(
                Transaction(
                    user_id=current_user.id,
                    account_id=account.id,
                    category_id=payment_category.id,
                    operation_type="expense",
                    amount=amount,
                    comment=f"Платеж: {payment.recipient}",
                )
            )
            flash("Платеж подтвержден и отражен в истории операций.", "success")
        else:
            flash("Платеж отклонен: недостаточно средств.", "error")

        db.session.commit()
        log_action(current_user.id, "payment_created", f"Payment {status}: {amount}")
        return redirect(url_for("main.payments"))

    payment_list = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).limit(30).all()
    return render_template("payments.html", form=form, payments=payment_list)


@main_bp.route("/analytics")
@login_required
def analytics():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    total_balance = sum((account.balance for account in accounts), Decimal("0.00"))
    income_total = sum((t.amount for t in transactions if t.operation_type == "income"), Decimal("0.00"))
    expense_total = sum((t.amount for t in transactions if t.operation_type == "expense"), Decimal("0.00"))

    category_expenses = defaultdict(Decimal)
    for item in transactions:
        if item.operation_type == "expense":
            category_expenses[item.category.name] += item.amount

    return render_template(
        "analytics.html",
        total_balance=total_balance,
        income_total=income_total,
        expense_total=expense_total,
        category_expenses=dict(category_expenses),
    )
