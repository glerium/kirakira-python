from datetime import date, datetime
from pathlib import Path

from plugins.kirakira.course_schedule import load_schedule

DATA_DIR = Path(__file__).parents[1] / "plugins" / "kirakira" / "data"


def test_teaching_week_and_split_sessions() -> None:
    schedule = load_schedule(DATA_DIR)
    assert schedule.teaching_week(date(2026, 8, 31)) == 1
    assert schedule.teaching_week(date(2026, 9, 7)) == 2
    assert schedule.teaching_week(date(2027, 1, 4)) is None

    occurrences = schedule.occurrences_for_date(date(2026, 9, 11))
    data_structures = [item for item in occurrences if item.course.course_id == "course-001"]
    assert [(item.start_period, item.end_period) for item in data_structures] == [(5, 6), (7, 8)]
    assert data_structures[0].start_at.strftime("%H:%M") == "14:00"


def test_reminder_window_and_period_end() -> None:
    schedule = load_schedule(DATA_DIR)
    occurrence = next(
        item
        for item in schedule.occurrences_for_date(date(2026, 11, 29))
        if item.course.course_id == "course-012" and item.start_period == 9
    )
    assert occurrence.end_at.strftime("%H:%M") == "21:50"
    due = schedule.reminder_due(datetime(2026, 11, 29, 18, 45, tzinfo=schedule.timezone))
    assert occurrence in due
