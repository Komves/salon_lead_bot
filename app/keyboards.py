from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.catalog import SERVICES, get_specialists


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


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить заявку", callback_data="lead_confirm")],
        [InlineKeyboardButton(text="Заполнить заново", callback_data="lead_restart")],
    ])


def admin_application_keyboard(application_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ответить клиенту", callback_data=f"admin_reply:{application_id}")],
        [
            InlineKeyboardButton(text="Подтвердить", callback_data=f"admin_confirm:{application_id}"),
            InlineKeyboardButton(text="Отклонить", callback_data=f"admin_decline:{application_id}"),
        ],
    ])
