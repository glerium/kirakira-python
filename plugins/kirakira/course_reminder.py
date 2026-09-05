from __future__ import annotations

from datetime import datetime

from nonebot import get_bots, logger
from nonebot_plugin_apscheduler import scheduler

from . import database
from .config import get_config
from .course_schedule import Occurrence, load_schedule


def format_reminder(occurrence: Occurrence) -> str:
    course = occurrence.course
    return (
        f"507上课提醒：15分钟后是{'、'.join(course.teachers)}老师的{course.name}，"
        f"上课时间为{occurrence.start_at:%H:%M}-{occurrence.end_at:%H:%M}，"
        f"班级为{course.class_name}，请注意安排实验室使用时间。"
    )


async def run_course_reminders(now: datetime | None = None) -> None:
    if not get_config().kirakira_enable_course_reminder:
        return
    bots = get_bots()
    if not bots:
        logger.warning("No OneBot connection; skipping course reminders")
        return
    bot = next(iter(bots.values()))
    schedule = load_schedule()
    for occurrence in schedule.reminder_due(now or datetime.now(schedule.timezone)):
        groups = await database.get_course_subscriber_groups(occurrence.course.teachers)
        for group_id in groups:
            if await database.course_reminder_sent(
                group_id,
                occurrence.course.course_id,
                occurrence.class_date,
                occurrence.start_period,
            ):
                continue
            try:
                await bot.send_group_msg(
                    group_id=int(group_id), message=format_reminder(occurrence)
                )
            except Exception:  # noqa: BLE001 - one failed group must not stop reminders
                logger.exception("Failed to send course reminder to group %s", group_id)
                continue
            await database.mark_course_reminder_sent(
                group_id,
                occurrence.course.course_id,
                occurrence.class_date,
                occurrence.start_period,
            )


@scheduler.scheduled_job(
    "interval", minutes=1, id="kirakira-course-reminder", max_instances=1, coalesce=True
)
async def course_reminder_job() -> None:
    await run_course_reminders()
