import asyncio
import os
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def migrate() -> None:
    sql = Path(__file__).parent / "schema.sql"
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    await conn.execute(sql.read_text())
    await conn.close()
    print("Migration complete.")


asyncio.run(migrate())
