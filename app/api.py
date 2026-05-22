from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.config import ADMIN_CHAT_ID
from app.catalog import CATALOG
from app.db import add_application_message, create_application
from app.keyboards import admin_application_keyboard

router = APIRouter()


class MiniAppApplication(BaseModel):
    tg_user_id: int
    username: str | None = None
    service: str
    specialist: str
    desired_date: str
    desired_time: str
    client_name: str
    phone: str


@router.get("/api/catalog")
async def get_catalog() -> dict:
    return {"catalog": CATALOG}


@router.post("/api/applications")
async def create_application_from_miniapp(payload: MiniAppApplication) -> dict:
    if payload.service not in CATALOG:
        raise HTTPException(status_code=400, detail="Unknown service")

    if payload.specialist not in CATALOG[payload.service]:
        raise HTTPException(status_code=400, detail="Unknown specialist for service")

    application_id = await create_application(payload.model_dump())
    await add_application_message(application_id, "client", "Заявка создана через Mini App")

    if ADMIN_CHAT_ID:
        username_line = f"Username: @{payload.username}" if payload.username else "Username: не указан"
        admin_text = (
            f"🆕 Новая заявка #{application_id}\n\n"
            f"Услуга: {payload.service}\n"
            f"Специалист: {payload.specialist}\n"
            f"Дата: {payload.desired_date}\n"
            f"Время: {payload.desired_time}\n\n"
            f"Клиент: {payload.client_name}\n"
            f"Телефон: {payload.phone}\n"
            f"Telegram ID: {payload.tg_user_id}\n"
            f"{username_line}"
        )
        from app.main import bot

        await bot.send_message(
            ADMIN_CHAT_ID,
            admin_text,
            reply_markup=admin_application_keyboard(application_id),
        )

        await bot.send_message(
            payload.tg_user_id,
            "✅ Заявка принята. Администратор проверит расписание и подтвердит запись.",
        )

    return {"status": "ok", "application_id": application_id}
