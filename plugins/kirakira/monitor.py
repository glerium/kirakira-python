from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import UTC, datetime
from typing import Protocol

from nonebot import get_bots, logger
from nonebot_plugin_apscheduler import scheduler

from . import database
from .codeforces import CodeforcesClient, CodeforcesError, CodeforcesUserNotFound
from .config import get_config


class MonitorRepository(Protocol):
    async def get_group_bindings(self) -> dict[str, list[str]]: ...
    async def user_finished_problem(self, cf_id: str, problem_id: str) -> bool: ...
    async def insert_submission(
        self, cf_id: str, problem_id: str, submission_id: str, submission_time: datetime
    ) -> None: ...
    async def remove_invalid_cf_id(self, cf_id: str) -> None: ...


async def check_submissions(
    bot: object,
    repository: MonitorRepository,
    client: CodeforcesClient,
    admin_group_id: str = "",
) -> None:
    logger.info("Checking submissions")
    notifications: dict[str, list[str]] = defaultdict(list)
    errors: dict[str, list[str]] = defaultdict(list)

    for cf_id, groups in (await repository.get_group_bindings()).items():
        logger.debug("Checking handle: {}", cf_id)
        try:
            submissions = await client.get_recent_accepted(cf_id)
        except CodeforcesUserNotFound as exc:
            for group_id in groups:
                errors[group_id].append(str(exc))
            await repository.remove_invalid_cf_id(cf_id)
            continue
        except CodeforcesError as exc:
            logger.warning("Codeforces API error for {}: {}", cf_id, exc)
            if admin_group_id:
                errors[admin_group_id].append(f"Codeforces API error for {cf_id}: {exc}")
            continue

        for submission in submissions:
            if await repository.user_finished_problem(cf_id, submission.problem_id):
                logger.debug("Skipping known problem {} for {}", submission.problem_id, cf_id)
                continue
            rating = "?" if submission.rating is None else str(submission.rating)
            message = f"{submission.display_handle} 通过了 {submission.problem_id} ({rating})。"
            for group_id in groups:
                notifications[group_id].append(message)
            await repository.insert_submission(
                cf_id,
                submission.problem_id,
                submission.submission_id,
                datetime.fromtimestamp(submission.creation_time_seconds, UTC).replace(tzinfo=None),
            )
            logger.info("Found accepted submission {} for {}", submission.problem_id, cf_id)

    group_ids = set(notifications) | set(errors)
    for index, group_id in enumerate(sorted(group_ids)):
        lines = notifications[group_id] + errors[group_id]
        if not lines:
            continue
        logger.info("Sending notification to group {}", group_id)
        await bot.send_group_msg(group_id=int(group_id), message="\n".join(lines))
        if index < len(group_ids) - 1:
            await asyncio.sleep(1)
    logger.info("Check submissions done")


@scheduler.scheduled_job("interval", minutes=5, id="kirakira-monitor")
async def scheduled_monitor() -> None:
    config = get_config()
    if not config.kirakira_enable_scheduler:
        return
    bots = get_bots()
    if not bots:
        logger.warning("Skipping monitor: no OneBot connection")
        return
    from . import get_codeforces_client

    await check_submissions(
        next(iter(bots.values())),
        database,
        get_codeforces_client(),
        config.kirakira_admin_group_id,
    )
