# app/auth/routes.py
from __future__ import annotations
from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user

from flask import session
from app.extensions import db, limiter
from app.models import Usuario
from . import auth_bp


def _valid_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1]


@auth_bp.get("/registro")
def register_form():
    if current_user.is_authenticated:
        return redirect(url_for("web.home"))
    return render_template("auth/register.html")


@auth_bp.post("/registro")
@limiter.limit("10 per hour")
def register_submit():
    email = (request.form.get("email", "") or "").strip().lower()
    nombre = (request.form.get("nombre", "") or "").strip()
    password = request.form.get("password", "") or ""
    password2 = request.form.get("password2", "") or ""

    error = None
    if not _valid_email(email):
        error = "Ingresa un correo válido."
    elif not nombre:
        error = "Ingresa tu nombre."
    elif len(password) < 10:
        error = "La contraseña debe tener al menos 10 caracteres."
    elif password != password2:
        error = "Las contraseñas no coinciden."
    elif Usuario.query.filter_by(email=email).first():
        error = "Ya existe una cuenta con ese correo."

    if error:
        return render_template("auth/register.html", error=error, email=email, nombre=nombre)

    user = Usuario(email=email, nombre=nombre, rol="usuario")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session.permanent = True
    login_user(user)
    return redirect(url_for("web.home"))


@auth_bp.get("/login")
def login_form():
    if current_user.is_authenticated:
        return redirect(url_for("web.home"))
    return render_template("auth/login.html")


@auth_bp.post("/login")
@limiter.limit("5 per 15 minutes")
def login_submit():
    email = (request.form.get("email", "") or "").strip().lower()
    password = request.form.get("password", "") or ""

    user = Usuario.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return render_template("auth/login.html", error="Correo o contraseña incorrectos.", email=email)

    if not user.is_active_account:
        # Mismo mensaje generico tambien aqui seria mas estricto, pero esta
        # distincion es operativa (el usuario sabe que debe contactar a un
        # admin en vez de reintentar su clave) y no revela si el correo existe
        # para quien NO tiene la clave correcta (ya paso el check_password).
        return render_template(
            "auth/login.html",
            error="Esta cuenta está deshabilitada. Contacta a un administrador.",
            email=email,
        )

    session.permanent = True
    login_user(user)
    next_url = request.args.get("next") or url_for("web.home")
    return redirect(next_url)


@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login_form"))