import asyncpg
import os
from datetime import datetime

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])


async def close_pool() -> None:
    if _pool:
        await _pool.close()


def pool() -> asyncpg.Pool:
    assert _pool is not None, "DB pool not initialised"
    return _pool


async def create_user(user_id: str) -> None:
    await pool().execute("INSERT INTO users (id) VALUES ($1)", user_id)


async def store_token(user_id: str, access_token: str, expires_at: datetime) -> None:
    await pool().execute(
        """
        INSERT INTO tokens (user_id, access_token, expires_at)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id)
        DO UPDATE SET access_token = $2, expires_at = $3
        """,
        user_id, access_token, expires_at,
    )


async def get_token(user_id: str) -> str | None:
    row = await pool().fetchrow(
        "SELECT access_token FROM tokens WHERE user_id = $1 AND expires_at > NOW()",
        user_id,
    )
    return row["access_token"] if row else None


async def revoke_token(user_id: str) -> None:
    await pool().execute("DELETE FROM tokens WHERE user_id = $1", user_id)


async def log_activity(user_id: str, tool_name: str) -> None:
    await pool().execute(
        "INSERT INTO activity_log (user_id, tool_name) VALUES ($1, $2)",
        user_id, tool_name,
    )


async def get_activity_log(user_id: str) -> list[dict]:
    rows = await pool().fetch(
        """
        SELECT tool_name, called_at
        FROM activity_log
        WHERE user_id = $1
        ORDER BY called_at DESC
        LIMIT 100
        """,
        user_id,
    )
    return [{"tool_name": r["tool_name"], "called_at": r["called_at"].isoformat()} for r in rows]
