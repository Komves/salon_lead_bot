import asyncpg

from app.config import DATABASE_URL

pool: asyncpg.Pool | None = None


def _require_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool is not initialized")
    return pool


async def init_db() -> None:
    global pool

    pool = await asyncpg.create_pool(DATABASE_URL)

    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            tg_user_id BIGINT NOT NULL,
            username TEXT,
            service TEXT NOT NULL,
            specialist TEXT NOT NULL,
            desired_date TEXT NOT NULL,
            desired_time TEXT NOT NULL,
            client_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            reminder_sent_at TEXT,
            client_reminder_response TEXT,
            client_reminder_response_at TEXT,
            cancelled_at TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS application_messages (
            id SERIAL PRIMARY KEY,
            application_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """)


async def create_application(data: dict) -> int:
    async with _require_pool().acquire() as conn:
        row = await conn.fetchrow("""
        INSERT INTO applications (
            tg_user_id, username, service, specialist,
            desired_date, desired_time, client_name, phone
        )
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        RETURNING id
        """,
            data["tg_user_id"],
            data.get("username"),
            data["service"],
            data["specialist"],
            data["desired_date"],
            data["desired_time"],
            data["client_name"],
            data["phone"],
        )
        return int(row["id"])


async def get_application(application_id: int) -> dict | None:
    async with _require_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM applications WHERE id = $1",
            application_id,
        )
        return dict(row) if row else None


async def update_application_status(application_id: int, status: str) -> None:
    async with _require_pool().acquire() as conn:
        await conn.execute(
            "UPDATE applications SET status = $1 WHERE id = $2",
            status,
            application_id,
        )


async def update_application_datetime(application_id: int, desired_date: str, desired_time: str) -> None:
    async with _require_pool().acquire() as conn:
        await conn.execute("""
        UPDATE applications
        SET desired_date = $1,
            desired_time = $2,
            reminder_sent_at = NULL,
            client_reminder_response = NULL,
            client_reminder_response_at = NULL,
            cancelled_at = NULL
        WHERE id = $3
        """, desired_date, desired_time, application_id)


async def mark_reminder_sent(application_id: int, sent_at: str) -> None:
    async with _require_pool().acquire() as conn:
        await conn.execute(
            "UPDATE applications SET reminder_sent_at = $1 WHERE id = $2",
            sent_at,
            application_id,
        )


async def update_client_reminder_response(
    application_id: int,
    response: str,
    status: str,
    response_at: str,
) -> None:
    cancelled_at = response_at if response == "will_not_come" else None

    async with _require_pool().acquire() as conn:
        await conn.execute("""
        UPDATE applications
        SET client_reminder_response = $1,
            client_reminder_response_at = $2,
            status = $3,
            cancelled_at = $4
        WHERE id = $5
        """, response, response_at, status, cancelled_at, application_id)


async def add_application_message(application_id: int, sender: str, text: str) -> None:
    async with _require_pool().acquire() as conn:
        await conn.execute("""
        INSERT INTO application_messages (application_id, sender, text)
        VALUES ($1,$2,$3)
        """, application_id, sender, text)


async def list_new_applications(limit: int = 10) -> list[dict]:
    async with _require_pool().acquire() as conn:
        rows = await conn.fetch("""
        SELECT * FROM applications
        WHERE status = 'new'
        ORDER BY id DESC
        LIMIT $1
        """, limit)
        return [dict(row) for row in rows]


async def list_confirmed_without_reminder() -> list[dict]:
    async with _require_pool().acquire() as conn:
        rows = await conn.fetch("""
        SELECT * FROM applications
        WHERE status = 'confirmed'
          AND reminder_sent_at IS NULL
        ORDER BY id ASC
        """)
        return [dict(row) for row in rows]


async def get_latest_open_application_by_user(tg_user_id: int) -> dict | None:
    async with _require_pool().acquire() as conn:
        row = await conn.fetchrow("""
        SELECT * FROM applications
        WHERE tg_user_id = $1
          AND status IN ('new', 'confirmed', 'client_confirmed')
        ORDER BY id DESC
        LIMIT 1
        """, tg_user_id)
        return dict(row) if row else None