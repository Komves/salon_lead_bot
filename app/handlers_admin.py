from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import ADMIN_CHAT_ID
from app.db import (
    add_application_message,
    get_application,
    list_new_applications,
    update_application_status,
)
from app.states import AdminReplyFlow

router = Router()


def is_admin(message_or_callback) -> bool:
    user_id = message_or_callback.from_user.id
    return bool(ADMIN_CHAT_ID and user_id == ADMIN_CHAT_ID)


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

    lines = ["Новые заявки:"]
    for app in apps:
        lines.append(
            f"#{app['id']} — {app['service']} / {app['specialist']} / "
            f"{app['desired_date']} {app['desired_time']} / {app['client_name']} / {app['phone']}"
        )
    await message.answer("\n".join(lines))
