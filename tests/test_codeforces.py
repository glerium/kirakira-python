import time

import httpx
import pytest

from plugins.kirakira import codeforces
from plugins.kirakira.codeforces import CodeforcesClient, CodeforcesError, CodeforcesUserNotFound


def make_client(
    payload: object, status_code: int = 200, request_interval_seconds: float = 0.0
) -> CodeforcesClient:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=payload)

    client = CodeforcesClient(request_interval_seconds=request_interval_seconds)
    client._client = httpx.AsyncClient(
        base_url="https://codeforces.com/api/",
        transport=httpx.MockTransport(handler),
    )
    return client


@pytest.mark.asyncio
async def test_recent_accepted_and_team_handle() -> None:
    now = int(time.time())
    client = make_client(
        {
            "status": "OK",
            "result": [
                {
                    "id": 1,
                    "verdict": "OK",
                    "creationTimeSeconds": now,
                    "problem": {"contestId": 1000, "index": "A", "rating": 800},
                    "author": {"members": [{"handle": "Tourist"}, {"handle": "friend"}]},
                }
            ],
        }
    )
    result = await client.get_recent_accepted("tourist")
    assert result[0].problem_id == "1000A"
    assert result[0].display_handle == "Tourist"
    await client.close()


@pytest.mark.asyncio
async def test_old_and_non_ok_submissions_are_ignored() -> None:
    client = make_client(
        {
            "status": "OK",
            "result": [
                {
                    "id": 1,
                    "verdict": "OK",
                    "creationTimeSeconds": int(time.time()) - 1900,
                    "problem": {"contestId": 1, "index": "A"},
                },
                {
                    "id": 2,
                    "verdict": "WRONG_ANSWER",
                    "creationTimeSeconds": int(time.time()),
                    "problem": {"contestId": 1, "index": "B"},
                },
            ],
        }
    )
    assert await client.get_recent_accepted("tourist") == []
    await client.close()


@pytest.mark.asyncio
async def test_user_not_found_and_api_failed() -> None:
    missing = make_client({"status": "FAILED", "comment": "handle: User with handle x not found"})
    with pytest.raises(CodeforcesUserNotFound):
        await missing.get_recent_accepted("x")
    await missing.close()

    failed = make_client({"status": "FAILED", "comment": "temporary failure"})
    with pytest.raises(CodeforcesError):
        await failed.get_recent_accepted("x")
    await failed.close()


@pytest.mark.asyncio
async def test_requests_are_globally_rate_limited(monkeypatch) -> None:
    client = make_client({"status": "OK", "result": []}, request_interval_seconds=2.0)
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(codeforces.asyncio, "sleep", fake_sleep)

    await client.get_recent_accepted("first")
    await client.get_recent_accepted("second")

    assert len(delays) == 1
    assert delays[0] >= 1.9
    await client.close()
