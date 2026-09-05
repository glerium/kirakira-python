from datetime import date, datetime

from plugins.kirakira.course_reminder import format_reminder, ordered_teachers
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
    assert message == (
        "507上课提醒：15分钟后是老师甲、老师乙老师的测试课程，"
        "上课时间为16:10-18:00，班级为测试班，请注意安排实验室使用时间。"
    )


def test_subscribed_teachers_are_listed_first() -> None:
    assert ordered_teachers(("老师甲", "老师乙", "老师丙"), {"老师乙"}) == (
        "老师乙",
        "老师甲",
        "老师丙",
    )
