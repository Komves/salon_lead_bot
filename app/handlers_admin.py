from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import ADMIN_CHAT_ID
from app.db import (
    add_application_message,
    get_application,
    list_new_applications,
    update_application_datetime,
    update_application_status,
)
from app.keyboards import admin_application_keyboard
from app.states import AdminEditTimeFlow, AdminReplyFlow

router = Router()


def is_admin(message_or_callback) -> bool:
    user_id = message_or_callback.from_user.id
    return bool(ADMIN_CHAT_ID and user_id == ADMIN_CHAT_ID)


def render_application(app: dict) -> str:
    username_line = f"Username: @{app['username']}" if app.get("username") else "Username: не указан"
    return (
        f"Заявка #{app['id']}\n\n"
        f"Статус: {app['status']}\n"
        f"Услуга: {app['service']}\n"
        f"Специалист: {app['specialist']}\n"
        f"Дата: {app['desired_date']}\n"
        f"Время: {app['desired_time']}\n\n"
        f"Клиент: {app['client_name']}\n"
        f"Телефон: {app['phone']}\n"
        f"Telegram ID: {app['tg_user_id']}\n"
        f"{username_line}"
    )


@router.callback_query(F.data.startswith("admin_reply:"))
async def admin_reply(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback):
        await callback.answer("Нет доступа", show_alert=True)
        return

    application_id = int(callback.data.split(":", 1)[1])
    app = await get_application(application_id)
    if not app:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await state.set_state(AdminReplyFlow.entering_message)
    await state.update_data(reply_application_id=application_id)
    await callback.message.answer(f"Напишите сообщение клиенту по заявке #{application_id}.")
    await callback.answer()


@router.message(AdminReplyFlow.entering_message)
async def send_admin_message_to_client(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return

    data = await state.get_data()
    application_id = int(data["reply_application_id"])
    app = await get_application(application_id)
    if not app:
        await message.answer("Заявка не найдена.")
        await state.clear()
        return

    await add_application_message(application_id, "admin", message.text)
    await message.bot.send_message(app["tg_user_id"], f"Сообщение администратора:\n\n{message.text}")
    await message.answer(f"Сообщение отправлено клиенту по заявке #{application_id}.")
    await state.clear()


@router.callback_query(F.data.startswith("admin_edit_time:"))
async def admin_edit_time(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback):
        await callback.answer("Нет доступа", show_alert=True)
        return

    application_id = int(callback.data.split(":", 1)[1])
    app = await get_application(application_id)
    if not app:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await state.set_state(AdminEditTimeFlow.entering_datetime)
    await state.update_data(edit_application_id=application_id)
    await callback.message.answer(
        "Введите новую дату и время одной строкой.\n"
        "Например: 25.05 17:30"
    )
    await callback.answer()


@router.message(AdminEditTimeFlow.entering_datetime)
async def save_edited_time(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return

    raw = message.text.strip()
    parts = raw.rsplit(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Не понял формат. Введите так: 25.05 17:30")
        return

    desired_date, desired_time = parts
    data = await state.get_data()
    application_id = int(data["edit_application_id"])

    await update_application_datetime(application_id, desired_date, desired_time)
    await add_application_message(application_id, "admin", f"Администратор изменил время на {desired_date} {desired_time}")

    app = await get_application(application_id)
    await message.bot.send_message(
        app["tg_user_id"],
        (
            "Администратор предложил другое время:\n\n"
            f"Дата: {desired_date}\n"
            f"Время: {desired_time}\n\n"
            "Если время подходит, напишите ответным сообщением."
        ),
    )
    await message.answer(
        "Дата/время обновлены и отправлены клиенту.\n\n"
        + render_application(app),
        reply_markup=admin_application_keyboard(application_id),
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm(callback: CallbackQuery) -> None:
    if not is_admin(callback):
        await callback.answer("Нет доступа", show_alert=True)
        return

    application_id = int(callback.data.split(":", 1)[1])
    app = await get_application(application_id)
    if not app:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await update_application_status(application_id, "confirmed")
    await callback.bot.send_message(
        app["tg_user_id"],
        (
            "✅ Ваша заявка подтверждена.\n\n"
            f"Услуга: {app['service']}\n"
            f"Специалист: {app['specialist']}\n"
            f"Дата: {app['desired_date']}\n"
            f"Время: {app['desired_time']}"
        ),
    )
    await callback.message.answer(f"Заявка #{application_id} подтверждена.")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_decline:"))
async def admin_decline(callback: CallbackQuery) -> None:
    if not is_admin(callback):
        await callback.answer("Нет доступа", show_alert=True)
        return

    application_id = int(callback.data.split(":", 1)[1])
    app = await get_application(application_id)
    if not app:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await update_application_status(application_id, "declined")
    await callback.bot.send_message(
        app["tg_user_id"],
        "❌ Заявка отклонена. Администратор свяжется с вами при необходимости.",
    )
    await callback.message.answer(f"Заявка #{application_id} отклонена.")
    await callback.answer()


@router.message(F.text == "/new")
async def show_new_applications(message: Message) -> None:
    if not is_admin(message):
        return

    apps = await list_new_applications()
    if not apps:
        await message.answer("Новых заявок нет.")
        return

    for app in apps:
        await message.answer(
            render_application(app),
            reply_markup=admin_application_keyboard(app["id"]),
        )
