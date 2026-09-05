from __future__ import annotations

import asyncio
import os
import time

import psutil

STARTED_AT = time.monotonic()


def _format_bytes(value: int) -> str:
    return f"{value / 1024 / 1024:.1f} MiB"


def _format_duration(seconds: float) -> str:
    total = int(seconds)
    days, remainder = divmod(total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    prefix = f"{days}天" if days else ""
    return f"{prefix}{hours:02d}:{minutes:02d}:{seconds:02d}"


async def get_status_message(bot_id: str) -> str:
    cpu_percent = await asyncio.to_thread(psutil.cpu_percent, 0.1)
    memory = psutil.virtual_memory()
    process_rss = psutil.Process(os.getpid()).memory_info().rss
    uptime = _format_duration(time.monotonic() - STARTED_AT)
    return (
        "KiraKira 状态\n"
        f"机器人在线：是（QQ {bot_id}）\n"
        f"在线时间：{uptime}\n"
        f"系统 CPU：{cpu_percent:.1f}%\n"
        f"系统内存：{_format_bytes(memory.used)} / {_format_bytes(memory.total)} "
        f"（{memory.percent:.1f}%）\n"
        f"机器人进程内存：{_format_bytes(process_rss)}"
    )
