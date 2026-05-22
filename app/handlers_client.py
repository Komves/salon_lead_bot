from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import ADMIN_CHAT_ID
from app.db import create_application, add_application_message
from app.keyboards import (
    admin_application_keyboard,
    confirm_keyboard,
    services_keyboard,
    specialists_keyboard,
)
from app.states import LeadFlow

router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(LeadFlow.choosing_service)
    await message.answer("Здравствуйте. Выберите услугу:", reply_markup=services_keyboard())


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
    await state.set_state(LeadFlow.entering_date)
    await callback.message.answer("Введите желаемую дату. Например: 25.05 или завтра")
    await callback.answer()


@router.message(LeadFlow.entering_date)
async def enter_date(message: Message, state: FSMContext) -> None:
    await state.update_data(desired_date=message.text.strip())
    await state.set_state(LeadFlow.entering_time)
    await message.answer("Введите желаемое время. Например: 15:00")


@router.message(LeadFlow.entering_time)
async def enter_time(message: Message, state: FSMContext) -> None:
    await state.update_data(desired_time=message.text.strip())
    await state.set_state(LeadFlow.entering_name)
    await message.answer("Введите ваше имя:")


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


@router.message()
async def fallback(message: Message, state: FSMContext) -> None:
    await message.answer("Для создания заявки нажмите /start")
