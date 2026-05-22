# salon_lead_bot

MVP Telegram-бота для приема заявок салона/парикмахерской.

## Запуск локально

```powershell
cd C:\ai_projects\salon_lead_bot
python -m venv v
.\v\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
python -m app.main
```

## Что делает

Клиент:
/start → услуга → специалист → дата → время → имя → телефон → подтверждение.

Админ:
получает заявку, может ответить клиенту, подтвердить или отклонить.

## Важно

Пока это не запись в слот, а заявка. Подтверждение делает только администратор.
