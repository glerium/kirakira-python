from datetime import date, datetime

from plugins.kirakira.course_reminder import format_reminder
from plugins.kirakira.course_schedule import Course, Occurrence


def test_reminder_message_contains_course_details() -> None:
    timezone = datetime.now().astimezone().tzinfo
    assert timezone is not None
    course = Course(
        "course-x", "测试课程", "测试班", "测试楼", ("老师甲", "老师乙"), frozenset({1}), ()
    )
    occurrence = Occurrence(
        course,
        date(2026, 8, 31),
        7,
        8,
        datetime(2026, 8, 31, 16, 10, tzinfo=timezone),
        datetime(2026, 8, 31, 18, 0, tzinfo=timezone),
        1,
    )
    message = format_reminder(occurrence)
    assert "15 分钟后上课" in message
    assert "16:10–18:00（第7-8节）" in message
    assert "老师甲、老师乙" in message
