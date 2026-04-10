"""
reminder.py
───────────
Background scheduler that periodically checks for upcoming/overdue todos
and sends WhatsApp reminders via Twilio.

Schedule: runs every REMINDER_INTERVAL_MINUTES (default: 30 min).
Reminder fires when a todo's due_date is within REMINDER_LEAD_MINUTES (default: 60 min).
"""

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════
#  WhatsApp sender
# ══════════════════════════════════════════
def send_whatsapp(app, to_number: str, message: str) -> bool:
    """Send a WhatsApp message via Twilio. Returns True on success."""
    with app.app_context():
        cfg = app.config
        sid   = cfg.get("TWILIO_ACCOUNT_SID", "")
        token = cfg.get("TWILIO_AUTH_TOKEN", "")
        from_ = cfg.get("WHATSAPP_FROM", "")

        if not all([sid, token, from_, to_number]):
            logger.warning("Twilio credentials or recipient number not configured — skipping WhatsApp.")
            return False

        try:
            client = Client(sid, token)
            client.messages.create(
                body=message,
                from_=from_,
                to=to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}",
            )
            logger.info("WhatsApp sent to %s", to_number)
            return True
        except TwilioRestException as exc:
            logger.error("Twilio error: %s", exc)
            return False


# ══════════════════════════════════════════
#  Reminder job  (called by the scheduler)
# ══════════════════════════════════════════
def check_and_send_reminders(app):
    """
    Finds todos that:
      - are NOT done
      - have NOT already had a reminder sent
      - are due within the next REMINDER_LEAD_MINUTES minutes  (or already overdue)
    Then sends a WhatsApp reminder to the owner's phone number.
    """
    from .models import db, Todo, User  # local import avoids circular deps

    with app.app_context():
        lead = app.config.get("REMINDER_LEAD_MINUTES", 60)
        now  = datetime.utcnow()
        soon = now + timedelta(minutes=lead)

        pending_todos = (
            Todo.query
            .filter(
                Todo.is_done        == False,
                Todo.reminder_sent  == False,
                Todo.due_date       != None,
                Todo.due_date       <= soon,
            )
            .all()
        )

        if not pending_todos:
            logger.debug("No pending reminders at %s", now.strftime("%H:%M"))
            return

        for todo in pending_todos:
            user = User.query.get(todo.user_id)
            if not user or not user.phone:
                logger.debug("Skipping todo #%d — user has no phone number.", todo.id)
                # Still mark sent so we don't keep retrying
                todo.reminder_sent = True
                continue

            overdue = todo.due_date < now
            time_label = (
                "is OVERDUE ⚠️"
                if overdue
                else f"is due at {todo.due_date.strftime('%I:%M %p')} ⏰"
            )

            message = (
                f"👋 Hi {user.name}!\n\n"
                f"📝 *Todo Reminder*\n"
                f"Task: *{todo.title}*\n"
                f"{'📋 ' + todo.description + chr(10) if todo.description else ''}"
                f"Priority: {todo.priority}\n"
                f"Status: This task {time_label}\n\n"
                f"Don't forget to complete it! ✅"
            )

            success = send_whatsapp(app, user.phone, message)
            if success:
                todo.reminder_sent = True

        db.session.commit()
        logger.info("Reminder job complete — processed %d todos.", len(pending_todos))


# ══════════════════════════════════════════
#  Scheduler setup
# ══════════════════════════════════════════
def start_scheduler(app):
    """Create and start the APScheduler background scheduler."""
    interval = app.config.get("REMINDER_INTERVAL_MINUTES", 30)

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        func=check_and_send_reminders,
        args=[app],
        trigger="interval",
        minutes=interval,
        id="reminder_job",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Reminder scheduler started — checking every %d minutes.", interval)
    return scheduler
