from types import SimpleNamespace

from plugins.kirakira import status


def test_format_duration() -> None:
    assert status._format_duration(3661) == "01:01:01"
    assert status._format_duration(90061) == "1天01:01:01"


async def test_status_message(monkeypatch) -> None:
    monkeypatch.setattr(status.psutil, "cpu_percent", lambda interval: 12.5)
    monkeypatch.setattr(
        status.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(used=512 * 1024 * 1024, total=1024 * 1024 * 1024, percent=50.0),
    )
    monkeypatch.setattr(
        status.psutil,
        "Process",
        lambda _: SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=64 * 1024 * 1024)),
    )
    monkeypatch.setattr(status, "STARTED_AT", status.time.monotonic() - 3661)

    message = await status.get_status_message("2035814839")

    assert "机器人在线：是（QQ 2035814839）" in message
    assert "在线时间：01:01:01" in message
    assert "系统 CPU：12.5%" in message
    assert "系统内存：512.0 MiB / 1024.0 MiB （50.0%）" in message
    assert "机器人进程内存：64.0 MiB" in message
