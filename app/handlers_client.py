from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import ADMIN_CHAT_ID, APP_TIMEZONE
from app.db import (
    add_application_message,
    create_application,
    get_application,
    get_latest_open_application_by_user,
    update_client_reminder_response,
)
from app.keyboards import (
    admin_application_keyboard,
    confirm_keyboard,
    dates_keyboard,
    services_keyboard,
    specialists_keyboard,
    start_keyboard,
    times_keyboard,
)
from app.states import LeadFlow

router = Router()


def now_iso() -> str:
    return datetime.now(ZoneInfo(APP_TIMEZONE)).isoformat(timespec="seconds")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Здравствуйте. Для записи откройте форму или заполните заявку прямо в чате.",
        reply_markup=start_keyboard(),
    )


@router.callback_query(F.data == "lead_restart")
async def restart(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(LeadFlow.choosing_service)
    await callback.message.answer("Выберите услугу:", reply_markup=services_keyboard())
    await callback.answer()


@router.callback_query(LeadFlow.choosing_service, F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext) -> None:
    service = callback.data.split(":", 1)[1]
    await state.update_data(service=service)
    await state.set_state(LeadFlow.choosing_specialist)
    await callback.message.answer("Выберите специалиста:", reply_markup=specialists_keyboard(service))
    await callback.answer()


@router.callback_query(LeadFlow.choosing_specialist, F.data.startswith("specialist:"))
async def choose_specialist(callback: CallbackQuery, state: FSMContext) -> None:
    specialist = callback.data.split(":", 1)[1]
    await state.update_data(specialist=specialist)
    await state.set_state(LeadFlow.choosing_date)
    await callback.message.answer("Выберите желаемую дату:", reply_markup=dates_keyboard(prefix="date"))
    await callback.answer()


@router.callback_query(LeadFlow.choosing_date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext) -> None:
    desired_date = callback.data.split(":", 1)[1]
    await state.update_data(desired_date=desired_date)
    await state.set_state(LeadFlow.choosing_time)
    await callback.message.answer("Выберите желаемое время:", reply_markup=times_keyboard(prefix="time"))
    await callback.answer()


@router.callback_query(LeadFlow.choosing_time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext) -> None:
    desired_time = callback.data.split(":", 1)[1]
    await state.update_data(desired_time=desired_time)
    await state.set_state(LeadFlow.entering_name)
    await callback.message.answer("Введите ваше имя:")
    await callback.answer()


@router.message(LeadFlow.entering_name)
async def enter_name(message: Message, state: FSMContext) -> None:
    await state.update_data(client_name=message.text.strip())
    await state.set_state(LeadFlow.entering_phone)
    await message.answer("Введите телефон:")


@router.message(LeadFlow.entering_phone)
async def enter_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text.strip())
    data = await state.get_data()
    await state.set_state(LeadFlow.confirming)

    text = (
        "Проверьте заявку:\n\n"
        f"Услуга: {data['service']}\n"
        f"Специалист: {data['specialist']}\n"
        f"Дата: {data['desired_date']}\n"
        f"Время: {data['desired_time']}\n"
        f"Имя: {data['client_name']}\n"
        f"Телефон: {data['phone']}"
    )
    await message.answer(text, reply_markup=confirm_keyboard())


@router.callback_query(LeadFlow.confirming, F.data == "lead_confirm")
async def confirm_lead(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user = callback.from_user

    application_id = await create_application({
        "tg_user_id": user.id,
        "username": user.username,
        "service": data["service"],
        "specialist": data["specialist"],
        "desired_date": data["desired_date"],
        "desired_time": data["desired_time"],
        "client_name": data["client_name"],
        "phone": data["phone"],
    })

    await add_application_message(application_id, "client", "Заявка создана")
    await callback.message.answer(
        "✅ Заявка принята. Администратор проверит расписание и подтвердит запись."
    )

    if ADMIN_CHAT_ID:
        username_line = f"Username: @{user.username}" if user.username else "Username: не указан"
        admin_text = (
            f"🆕 Новая заявка #{application_id}\n\n"
            f"Услуга: {data['service']}\n"
            f"Специалист: {data['specialist']}\n"
            f"Дата: {data['desired_date']}\n"
            f"Время: {data['desired_time']}\n\n"
            f"Клиент: {data['client_name']}\n"
            f"Телефон: {data['phone']}\n"
            f"Telegram ID: {user.id}\n"
            f"{username_line}"
        )
        await callback.bot.send_message(
            ADMIN_CHAT_ID,
            admin_text,
            reply_markup=admin_application_keyboard(application_id),
        )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("client_will_come:"))
async def client_will_come(callback: CallbackQuery) -> None:
    application_id = int(callback.data.split(":", 1)[1])
    app = await get_application(application_id)
    if not app or app["tg_user_id"] != callback.from_user.id:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await update_client_reminder_response(application_id, "will_come", "client_confirmed", now_iso())
    await add_application_message(application_id, "client", "Клиент подтвердил, что придет")
    await callback.message.answer("✅ Спасибо, ждём вас в назначенное время.")

    if ADMIN_CHAT_ID:
        await callback.bot.send_message(
            ADMIN_CHAT_ID,
            (
                f"✅ Клиент подтвердил визит по заявке #{application_id}\n\n"
                f"Услуга: {app['service']}\n"
                f"Специалист: {app['specialist']}\n"
                f"Дата: {app['desired_date']}\n"
                f"Время: {app['desired_time']}\n\n"
                f"Клиент: {app['client_name']}\n"
                f"Телефон: {app['phone']}"
            ),
            reply_markup=admin_application_keyboard(application_id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("client_will_not_come:"))
async def client_will_not_come(callback: CallbackQuery) -> None:
    application_id = int(callback.data.split(":", 1)[1])
    app = await get_application(application_id)
    if not app or app["tg_user_id"] != callback.from_user.id:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await update_client_reminder_response(application_id, "will_not_come", "cancelled_by_client", now_iso())
    await add_application_message(application_id, "client", "Клиент отменил визит через напоминание")
    await callback.message.answer("❌ Запись отменена. Администратор получил уведомление.")

    if ADMIN_CHAT_ID:
        await callback.bot.send_message(
            ADMIN_CHAT_ID,
            (
                f"❌ Клиент отменил запись #{application_id}\n\n"
                f"Услуга: {app['service']}\n"
                f"Специалист: {app['specialist']}\n"
                f"Дата: {app['desired_date']}\n"
                f"Время: {app['desired_time']}\n\n"
                f"Клиент: {app['client_name']}\n"
                f"Телефон: {app['phone']}"
            ),
            reply_markup=admin_application_keyboard(application_id),
        )
    await callback.answer()


@router.message()
async def fallback(message: Message, state: FSMContext) -> None:
    active_app = await get_latest_open_application_by_user(message.from_user.id)

    if active_app and ADMIN_CHAT_ID:
        await add_application_message(active_app["id"], "client", message.text)
        await message.bot.send_message(
            ADMIN_CHAT_ID,
            (
                f"Сообщение клиента по заявке #{active_app['id']}:\n\n"
                f"{message.text}"
            ),
            reply_markup=admin_application_keyboard(active_app["id"]),
        )
        await message.answer("Сообщение передано администратору.")
        return

    await message.answer("Для создания заявки нажмите /start")
