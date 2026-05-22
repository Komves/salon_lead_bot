import os
import aiosqlite
from app.config import DATABASE_PATH


async def init_db() -> None:
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_user_id INTEGER NOT NULL,
            username TEXT,
            service TEXT NOT NULL,
            specialist TEXT NOT NULL,
            desired_date TEXT NOT NULL,
            desired_time TEXT NOT NULL,
            client_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS application_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await db.commit()


async def create_application(data: dict) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
        INSERT INTO applications (
            tg_user_id, username, service, specialist,
            desired_date, desired_time, client_name, phone
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["tg_user_id"],
            data.get("username"),
            data["service"],
            data["specialist"],
            data["desired_date"],
            data["desired_time"],
            data["client_name"],
            data["phone"],
        ))
        await db.commit()
        return int(cursor.lastrowid)


async def get_application(application_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM applications WHERE id = ?", (application_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_application_status(application_id: int, status: str) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE applications SET status = ? WHERE id = ?", (status, application_id))
        await db.commit()


async def add_application_message(application_id: int, sender: str, text: str) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO application_messages (application_id, sender, text) VALUES (?, ?, ?)",
            (application_id, sender, text),
        )
        await db.commit()


async def list_new_applications(limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM applications WHERE status = 'new' ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
