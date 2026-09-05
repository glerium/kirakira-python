from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime

import asyncmy

from .config import Config

_pool: asyncmy.Pool | None = None
_binding_lock = asyncio.Lock()


async def init_pool(config: Config) -> None:
    global _pool
    _pool = await asyncmy.create_pool(
        host=config.mysql_host,
        port=config.mysql_port,
        user=config.mysql_user,
        password=config.mysql_password,
        db=config.mysql_database,
        autocommit=True,
        minsize=1,
        maxsize=5,
        charset="utf8mb4",
    )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


def _require_pool() -> asyncmy.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool


async def cf_id_exists_in_group(group_id: str, cf_id: str) -> bool:
    pool = _require_pool()
    async with pool.acquire() as conn, conn.cursor() as cursor:
        await cursor.execute(
            "SELECT 1 FROM group_user WHERE group_id=%s AND LOWER(codeforces_id)=LOWER(%s) LIMIT 1",
            (group_id, cf_id),
        )
        return await cursor.fetchone() is not None


async def binding_exists(group_id: str, user_id: str, cf_id: str) -> bool:
    pool = _require_pool()
    async with pool.acquire() as conn, conn.cursor() as cursor:
        await cursor.execute(
            "SELECT 1 FROM group_user WHERE group_id=%s AND user_qq_id=%s "
            "AND LOWER(codeforces_id)=LOWER(%s) LIMIT 1",
            (group_id, user_id, cf_id),
        )
        return await cursor.fetchone() is not None


async def add_binding(group_id: str, user_id: str, cf_id: str) -> bool:
    async with _binding_lock:
        if await cf_id_exists_in_group(group_id, cf_id):
            return False
        pool = _require_pool()
        async with pool.acquire() as conn, conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO group_user (group_id, user_qq_id, codeforces_id) VALUES (%s, %s, %s)",
                (group_id, user_id, cf_id),
            )
    return True


async def remove_binding(group_id: str, user_id: str, cf_id: str) -> bool:
    pool = _require_pool()
    async with pool.acquire() as conn, conn.cursor() as cursor:
        await cursor.execute(
            "DELETE FROM group_user WHERE group_id=%s AND user_qq_id=%s "
            "AND LOWER(codeforces_id)=LOWER(%s)",
            (group_id, user_id, cf_id),
        )
        return cursor.rowcount > 0


async def get_user_cf_ids(group_id: str, user_id: str) -> list[str]:
    pool = _require_pool()
    async with pool.acquire() as conn, conn.cursor() as cursor:
        await cursor.execute(
            "SELECT codeforces_id FROM group_user WHERE group_id=%s AND user_qq_id=%s ORDER BY codeforces_id",
            (group_id, user_id),
        )
        return [str(row[0]) for row in await cursor.fetchall()]


async def get_group_bindings() -> dict[str, list[str]]:
    pool = _require_pool()
    async with pool.acquire() as conn, conn.cursor() as cursor:
        await cursor.execute("SELECT codeforces_id, group_id FROM group_user")
        result: dict[str, list[str]] = defaultdict(list)
        for cf_id, group_id in await cursor.fetchall():
            key = str(cf_id).lower()
            if str(group_id) not in result[key]:
                result[key].append(str(group_id))
        return dict(result)


async def get_groups_by_cf_id(cf_id: str) -> list[str]:
    pool = _require_pool()
    async with pool.acquire() as conn, conn.cursor() as cursor:
        await cursor.execute(
            "SELECT DISTINCT group_id FROM group_user WHERE LOWER(codeforces_id)=LOWER(%s)",
            (cf_id,),
        )
        return [str(row[0]) for row in await cursor.fetchall()]


async def user_finished_problem(cf_id: str, problem_id: str) -> bool:
    pool = _require_pool()
    async with pool.acquire() as conn, conn.cursor() as cursor:
        await cursor.execute(
            "SELECT 1 FROM submission WHERE LOWER(codeforces_id)=LOWER(%s) AND problem_id=%s LIMIT 1",
            (cf_id, problem_id),
        )
        return await cursor.fetchone() is not None


async def insert_submission(
    cf_id: str, problem_id: str, submission_id: str, submission_time: datetime
) -> None:
    pool = _require_pool()
    async with pool.acquire() as conn, conn.cursor() as cursor:
        await cursor.execute(
            "INSERT INTO submission (codeforces_id, problem_id, submission_id, submission_time) VALUES (%s, %s, %s, %s)",
            (cf_id, problem_id, submission_id, submission_time),
        )


async def remove_invalid_cf_id(cf_id: str) -> None:
    pool = _require_pool()
    async with pool.acquire() as conn, conn.cursor() as cursor:
        await cursor.execute(
            "DELETE FROM group_user WHERE LOWER(codeforces_id)=LOWER(%s)", (cf_id,)
        )


async def get_bindings_in_group(group_id: str) -> list[tuple[str, str]]:
    pool = _require_pool()
    async with pool.acquire() as conn, conn.cursor() as cursor:
        await cursor.execute(
            "SELECT user_qq_id, codeforces_id FROM group_user WHERE group_id=%s "
            "ORDER BY user_qq_id, codeforces_id",
            (group_id,),
        )
        return [(str(user_id), str(cf_id)) for user_id, cf_id in await cursor.fetchall()]
