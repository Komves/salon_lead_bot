# salon_lead_bot

MVP Telegram-бота для приема заявок салона/парикмахерской.

## V2: Bot + Mini App

Клиентская запись доступна двумя способами:

1. Mini App по кнопке `/start`.
2. Заполнение заявки прямо в чате через inline-кнопки.

Админская часть остается в Telegram: заявка, ответ клиенту, изменение даты/времени, подтверждение/отклонение.

## Локальный запуск

```powershell
python -m venv v
.\Scriptsctivate
pip install -r requirements.txt
copy .env.example .env
notepad .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Render

Тип сервиса теперь: **Web Service**, не Background Worker.

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment Variables:

```env
BOT_TOKEN=...
ADMIN_CHAT_ID=...
DATABASE_PATH=data/bot.db
PUBLIC_BASE_URL=https://your-render-service.onrender.com
PYTHON_VERSION=3.11.9
```

Важно: `PUBLIC_BASE_URL` должен быть HTTPS-адресом Render Web Service. Иначе Telegram Mini App не откроется.
