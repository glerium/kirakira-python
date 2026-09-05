from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any

import httpx


class CodeforcesError(Exception):
    pass


class CodeforcesUserNotFound(CodeforcesError):
    pass


@dataclass(frozen=True)
class Submission:
    submission_id: str
    problem_id: str
    rating: int | None
    creation_time_seconds: int
    display_handle: str


class CodeforcesClient:
    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://codeforces.com/api/",
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_recent_accepted(self, handle: str) -> list[Submission]:
        try:
            response = await self._client.get(
                "user.status",
                params={"handle": handle, "from": 1, "count": 10},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise CodeforcesError(f"Codeforces request failed: {exc}") from exc

        if not isinstance(payload, dict):
            raise CodeforcesError("Codeforces returned a non-object response")
        if payload.get("status") == "FAILED":
            comment = str(payload.get("comment", "Codeforces API failed"))
            if "handle" in comment.lower() and "not found" in comment.lower():
                raise CodeforcesUserNotFound(f"Codeforces 用户 {handle} 不存在")
            raise CodeforcesError(comment)
        if payload.get("status") != "OK" or not isinstance(payload.get("result"), list):
            raise CodeforcesError("Codeforces response is missing a valid result")

        cutoff = int(time()) - 30 * 60
        accepted: list[Submission] = []
        for item in payload["result"]:
            submission = self._parse_submission(item, handle)
            if submission and submission.creation_time_seconds >= cutoff:
                accepted.append(submission)
        return accepted

    @staticmethod
    def _parse_submission(item: Any, requested_handle: str) -> Submission | None:
        if not isinstance(item, dict) or item.get("verdict") != "OK":
            return None
        problem = item.get("problem")
        if not isinstance(problem, dict):
            return None
        contest_id, index = problem.get("contestId"), problem.get("index")
        created, submission_id = item.get("creationTimeSeconds"), item.get("id")
        if contest_id is None or not index or created is None or submission_id is None:
            return None

        display_handle = requested_handle
        author = item.get("author")
        members = author.get("members", []) if isinstance(author, dict) else []
        for member in members:
            if (
                isinstance(member, dict)
                and str(member.get("handle", "")).lower() == requested_handle.lower()
            ):
                display_handle = str(member["handle"])
                break

        rating = problem.get("rating")
        return Submission(
            submission_id=str(submission_id),
            problem_id=f"{contest_id}{index}",
            rating=int(rating) if isinstance(rating, int) else None,
            creation_time_seconds=int(created),
            display_handle=display_handle,
        )
