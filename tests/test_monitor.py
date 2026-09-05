import time
from dataclasses import dataclass, field

import pytest

from plugins.kirakira.codeforces import CodeforcesError, CodeforcesUserNotFound, Submission
from plugins.kirakira.monitor import check_submissions


@dataclass
class FakeRepository:
    bindings: dict[str, list[str]]
    known: set[tuple[str, str]] = field(default_factory=set)
    removed: list[str] = field(default_factory=list)

    async def get_group_bindings(self) -> dict[str, list[str]]:
        return self.bindings

    async def user_finished_problem(self, cf_id: str, problem_id: str) -> bool:
        return (cf_id, problem_id) in self.known

    async def insert_submission(self, cf_id: str, problem_id: str, *_: object) -> None:
        self.known.add((cf_id, problem_id))

    async def remove_invalid_cf_id(self, cf_id: str) -> None:
        self.removed.append(cf_id)


@dataclass
class FakeBot:
    sent: list[tuple[int, str]] = field(default_factory=list)

    async def send_group_msg(self, *, group_id: int, message: str) -> None:
        self.sent.append((group_id, message))


class FakeClient:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses

    async def get_recent_accepted(self, handle: str) -> list[Submission]:
        value = self.responses[handle]
        if isinstance(value, Exception):
            raise value
        return value  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_monitor_notifies_every_bound_group_once() -> None:
    submission = Submission("1", "1000A", 800, int(time.time()), "Tourist")
    repo = FakeRepository({"tourist": ["1", "2"]})
    bot = FakeBot()
    await check_submissions(bot, repo, FakeClient({"tourist": [submission]}))
    assert {group_id for group_id, _ in bot.sent} == {1, 2}

    bot.sent.clear()
    await check_submissions(bot, repo, FakeClient({"tourist": [submission]}))
    assert bot.sent == []


@pytest.mark.asyncio
async def test_monitor_reports_errors_without_submission() -> None:
    repo = FakeRepository({"missing": ["1"], "broken": ["2"]})
    bot = FakeBot()
    await check_submissions(
        bot,
        repo,
        FakeClient({"missing": CodeforcesUserNotFound("missing"), "broken": CodeforcesError("timeout")}),
        admin_group_id="99",
    )
    assert repo.removed == ["missing"]
    assert {group_id for group_id, _ in bot.sent} == {1, 99}
