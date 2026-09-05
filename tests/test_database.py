from dataclasses import dataclass

import pytest

from plugins.kirakira import database


@dataclass
class Resource:
    value: object

    async def __aenter__(self) -> object:
        return self.value

    async def __aexit__(self, *_: object) -> None:
        return None


class Cursor:
    async def execute(self, *_: object) -> None:
        return None

    async def fetchall(self) -> list[tuple[str, str]]:
        return [("Tourist", "A"), ("tourist", "B"), ("TOURIST", "A")]


class Connection:
    def cursor(self) -> Resource:
        return Resource(Cursor())


class Pool:
    def acquire(self) -> Resource:
        return Resource(Connection())


@pytest.mark.asyncio
async def test_group_bindings_normalize_handle_case(monkeypatch) -> None:
    monkeypatch.setattr(database, "_pool", Pool())

    assert await database.get_group_bindings() == {"tourist": ["A", "B"]}
