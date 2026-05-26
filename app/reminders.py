import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot

from app.config import APP_TIMEZONE, REMINDER_MINUTES_BEFORE
from app.db import add_application_message, list_confirmed_without_reminder, mark_reminder_sent
from app.keyboards import reminder_response_keyboard

logger = logging.getLogger(__name__)


def parse_appointment_at(app: dict) -> datetime | None:
    raw = f"{app['desired_date']} {app['desired_time']}".strip()
    tz = ZoneInfo(APP_TIMEZONE)
    formats = [
        "%d.%m.%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%d,%m,%Y %H:%M",
        "%d.%m.%Y %H-%M",
        "%d/%m/%Y %H-%M",
        "%d,%m,%Y %H-%M",
        "%d.%m %H:%M",
        "%d/%m %H:%M",
        "%d,%m %H:%M",
        "%d.%m %H-%M",
        "%d/%m %H-%M",
        "%d,%m %H-%M",
    ]
    current_year = datetime.now(tz).year
    for fmt in formats:
        try:
            dt = datetime.strptime(raw, fmt)
            if "%Y" not in fmt:
                dt = dt.replace(year=current_year)
            return dt.replace(tzinfo=tz)
        except ValueError:
            continue
    logger.warning("Cannot parse appointment datetime for application %s: %s", app.get("id"), raw)
    return None


async def send_due_reminders(bot: Bot) -> None:
    tz = ZoneInfo(APP_TIMEZONE)
    now = datetime.now(tz)
    apps = await list_confirmed_without_reminder()

    print(
        "[REMINDER_LOOP]",
        "now=", now.isoformat(),
        "timezone=", APP_TIMEZONE,
        "minutes_before=", REMINDER_MINUTES_BEFORE,
        "apps_count=", len(apps),
        flush=True,
    )

    for app in apps:
        print(
            "[REMINDER_APP]",
            "app_id=", app.get("id"),
            "status=", app.get("status"),
            "date=", app.get("desired_date"),
            "time=", app.get("desired_time"),
            "reminder_sent_at=", app.get("reminder_sent_at"),
            flush=True,
        )

        appointment_at = parse_appointment_at(app)
        if not appointment_at:
            print("[REMINDER_SKIP] reason=parse_failed app_id=", app.get("id"), flush=True)
            continue

        minutes_left = (appointment_at - now).total_seconds() / 60

        print(
            "[REMINDER_TIME]",
            "app_id=", app.get("id"),
            "appointment_at=", appointment_at.isoformat(),
            "minutes_left=", minutes_left,
            flush=True,
        )

        # запись уже прошла
        if minutes_left < 0:
            print("[REMINDER_SKIP] reason=already_past app_id=", app.get("id"), flush=True)
            continue

        # еще слишком рано
        if minutes_left > REMINDER_MINUTES_BEFORE:
            print("[REMINDER_SKIP] reason=too_early app_id=", app.get("id"), flush=True)
            continue

        # защита от позднего пробуждения Render
        # не шлем если осталось меньше 5 минут
        if minutes_left < 5:
            print("[REMINDER_SKIP] reason=too_late app_id=", app.get("id"), flush=True)
            continue

        print(
            "[REMINDER_SEND]",
            "app_id=", app["id"],
            "now=", now.isoformat(),
            "appointment_at=", appointment_at.isoformat(),
            "minutes_left=", minutes_left,
            flush=True,
        )

        text = (
            "✨ Напоминаем о вашей записи\n\n"
            f"📅 {app['desired_date']} в {app['desired_time']}\n"
            f"💇 Услуга: {app['service']}\n"
            f"👤 Специалист: {app['specialist']}\n\n"
            "Мы будем вас ждать.\n"
            "Пожалуйста, подтвердите, сможете ли прийти."
        )

        await bot.send_message(
            app["tg_user_id"],
            text,
            reply_markup=reminder_response_keyboard(app["id"]),
        )

        await mark_reminder_sent(app["id"], now.isoformat(timespec="seconds"))

        await add_application_message(
            app["id"],
            "system",
            "Отправлено напоминание за час",
        )


async def reminder_loop(bot: Bot) -> None:
    while True:
        try:
            await send_due_reminders(bot)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Reminder loop error")
        await asyncio.sleep(60)
