from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ══════════════════════════════════════════
#  User Model
# ══════════════════════════════════════════
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(150), unique=True, nullable=False)
    password_hash= db.Column(db.String(256), nullable=False)
    phone        = db.Column(db.String(20), nullable=True)   # WhatsApp number
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: one user → many todos
    todos        = db.relationship("Todo", backref="owner", lazy=True,
                                   cascade="all, delete-orphan")

    # ── Password helpers ───────────────────────────────
    def set_password(self, raw_password: str):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.email}>"


# ══════════════════════════════════════════
#  Todo Model
# ══════════════════════════════════════════
class Todo(db.Model):
    __tablename__ = "todos"

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title           = db.Column(db.String(200), nullable=False)
    description     = db.Column(db.Text, nullable=True)
    due_date        = db.Column(db.DateTime, nullable=True)
    priority        = db.Column(db.String(10), default="Medium")  # High / Medium / Low
    is_done         = db.Column(db.Boolean, default=False)
    reminder_sent   = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """Serialise to JSON-friendly dict for the API."""
        return {
            "id"           : self.id,
            "title"        : self.title,
            "description"  : self.description or "",
            "due_date"     : self.due_date.strftime("%Y-%m-%dT%H:%M") if self.due_date else None,
            "priority"     : self.priority,
            "is_done"      : self.is_done,
            "reminder_sent": self.reminder_sent,
            "created_at"   : self.created_at.strftime("%Y-%m-%d %H:%M"),
        }

    def __repr__(self):
        return f"<Todo {self.title!r} user={self.user_id}>"
