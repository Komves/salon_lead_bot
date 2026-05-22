from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.config import PUBLIC_BASE_URL

from app.catalog import SERVICES, get_specialists


TIME_SLOTS = [
    "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "13:00", "13:30",
    "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30", "17:00", "17:30",
    "18:00", "18:30", "19:00", "19:30",
]


RU_WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def start_keyboard() -> InlineKeyboardMarkup:
    rows = []
    if PUBLIC_BASE_URL:
        rows.append([
            InlineKeyboardButton(
                text="Открыть форму записи",
                web_app=WebAppInfo(url=PUBLIC_BASE_URL),
            )
        ])
    rows.append([InlineKeyboardButton(text="Заполнить в чате", callback_data="lead_restart")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def services_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=service, callback_data=f"service:{service}")]
        for service in SERVICES
    ])


def specialists_keyboard(service: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"specialist:{name}")]
        for name in get_specialists(service)
    ])


def dates_keyboard(prefix: str = "date", days: int = 14) -> InlineKeyboardMarkup:
    today = date.today()
    rows = []
    row = []

    for offset in range(days):
        current = today + timedelta(days=offset)
        value = current.strftime("%d.%m.%Y")
        label = f"{RU_WEEKDAYS[current.weekday()]} {current.strftime('%d.%m')}"
        row.append(InlineKeyboardButton(text=label, callback_data=f"{prefix}:{value}"))

        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def times_keyboard(prefix: str = "time") -> InlineKeyboardMarkup:
    rows = []
    row = []

    for slot in TIME_SLOTS:
        row.append(InlineKeyboardButton(text=slot, callback_data=f"{prefix}:{slot}"))
        if len(row) == 4:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить заявку", callback_data="lead_confirm")],
        [InlineKeyboardButton(text="Заполнить заново", callback_data="lead_restart")],
    ])


def admin_application_keyboard(application_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ответить клиенту", callback_data=f"admin_reply:{application_id}")],
        [InlineKeyboardButton(text="Изменить дату/время", callback_data=f"admin_edit_time:{application_id}")],
        [
            InlineKeyboardButton(text="Подтвердить", callback_data=f"admin_confirm:{application_id}"),
            InlineKeyboardButton(text="Отклонить", callback_data=f"admin_decline:{application_id}"),
        ],
    ])
