from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from .models import db, Todo

todos_bp = Blueprint("todos", __name__)


# ──────────────────────────────────────────
#  GET /dashboard  — Serve the main UI
# ──────────────────────────────────────────
@todos_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


# ──────────────────────────────────────────
#  GET /todos  — List all todos for user
# ──────────────────────────────────────────
@todos_bp.route("/todos", methods=["GET"])
@login_required
def get_todos():
    todos = (
        Todo.query
        .filter_by(user_id=current_user.id)
        .order_by(Todo.created_at.desc())
        .all()
    )
    return jsonify({"success": True, "todos": [t.to_dict() for t in todos]})


# ──────────────────────────────────────────
#  POST /todos  — Create a new todo
# ──────────────────────────────────────────
@todos_bp.route("/todos", methods=["POST"])
@login_required
def create_todo():
    data        = request.get_json()
    title       = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    priority    = data.get("priority", "Medium")
    due_date_str= data.get("due_date") or ""

    if not title:
        return jsonify({"success": False, "message": "Title is required."}), 400

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            return jsonify({"success": False, "message": "Invalid due date format."}), 400

    todo = Todo(
        user_id     = current_user.id,
        title       = title,
        description = description,
        priority    = priority,
        due_date    = due_date,
    )
    db.session.add(todo)
    db.session.commit()

    return jsonify({"success": True, "message": "Todo created.", "todo": todo.to_dict()}), 201


# ──────────────────────────────────────────
#  PUT /todos/<id>  — Update / toggle done
# ──────────────────────────────────────────
@todos_bp.route("/todos/<int:todo_id>", methods=["PUT"])
@login_required
def update_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
    if not todo:
        return jsonify({"success": False, "message": "Todo not found."}), 404

    data = request.get_json()

    if "title" in data:
        todo.title = (data["title"] or "").strip() or todo.title
    if "description" in data:
        todo.description = data["description"]
    if "priority" in data:
        todo.priority = data["priority"]
    if "is_done" in data:
        todo.is_done = bool(data["is_done"])
    if "due_date" in data and data["due_date"]:
        try:
            todo.due_date = datetime.strptime(data["due_date"], "%Y-%m-%dT%H:%M")
            todo.reminder_sent = False   # reset so reminder fires again if rescheduled
        except ValueError:
            return jsonify({"success": False, "message": "Invalid due date format."}), 400

    db.session.commit()
    return jsonify({"success": True, "message": "Todo updated.", "todo": todo.to_dict()})


# ──────────────────────────────────────────
#  DELETE /todos/<id>  — Remove a todo
# ──────────────────────────────────────────
@todos_bp.route("/todos/<int:todo_id>", methods=["DELETE"])
@login_required
def delete_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
    if not todo:
        return jsonify({"success": False, "message": "Todo not found."}), 404

    db.session.delete(todo)
    db.session.commit()
    return jsonify({"success": True, "message": "Todo deleted."})
