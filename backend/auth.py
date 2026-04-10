from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User

auth_bp = Blueprint("auth", __name__)


# ──────────────────────────────────────────
#  Show Login Page
# ──────────────────────────────────────────
@auth_bp.route("/", methods=["GET"])
@auth_bp.route("/login", methods=["GET"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("todos.dashboard"))
    return render_template("login.html")


# ──────────────────────────────────────────
#  Show Register Page
# ──────────────────────────────────────────
@auth_bp.route("/register", methods=["GET"])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("todos.dashboard"))
    return render_template("register.html")


# ──────────────────────────────────────────
#  POST /auth/login  — Authenticate user
# ──────────────────────────────────────────
@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    login_user(user, remember=True)
    return jsonify({"success": True, "message": "Login successful.", "name": user.name})


# ──────────────────────────────────────────
#  POST /auth/register  — Create new account
# ──────────────────────────────────────────
@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    phone    = (data.get("phone") or "").strip()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"success": False, "message": "Name, email, and password are required."}), 400

    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "An account with this email already exists."}), 409

    new_user = User(name=name, email=email, phone=phone)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user, remember=True)
    return jsonify({"success": True, "message": "Account created successfully.", "name": new_user.name}), 201


# ──────────────────────────────────────────
#  GET /auth/logout  — End session
# ──────────────────────────────────────────
@auth_bp.route("/auth/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login_page"))
