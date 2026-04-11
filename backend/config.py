import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # ── Flask ──────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # ── Database ───────────────────────────────────────
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Use Supabase (PostgreSQL) if available, else fallback to SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Twilio WhatsApp ────────────────────────────────
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO", "")

    # ── Reminder Scheduler ─────────────────────────────
    REMINDER_INTERVAL_MINUTES = 30
    REMINDER_LEAD_MINUTES = 60
