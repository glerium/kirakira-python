from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

DATA_DIR = Path(__file__).parent / "data"


@dataclass(frozen=True)
class Course:
    course_id: str
    name: str
    class_name: str
    location: str
    teachers: tuple[str, ...]
    weeks: frozenset[int]
    sessions: tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class Occurrence:
    course: Course
    class_date: date
    start_period: int
    end_period: int
    start_at: datetime
    end_at: datetime
    week: int


class CourseSchedule:
    def __init__(self, timetable: dict, periods: dict) -> None:
        semester = timetable["semester"]
        self.start_date = date.fromisoformat(str(semester["start_date"]))
        self.total_weeks = int(semester["total_weeks"])
        self.timezone = ZoneInfo(str(semester.get("timezone", periods["timezone"])))
        self.reminder_minutes = int(periods["reminder_minutes"])
        self.periods = {
            int(number): (time.fromisoformat(value["start"]), time.fromisoformat(value["end"]))
            for number, value in periods["periods"].items()
        }
        self.courses = tuple(
            Course(
                course_id=str(row["id"]),
                name=str(row["name"]),
                class_name=str(row["class_name"]),
                location=str(row["location"]),
                teachers=tuple(str(teacher) for teacher in row["teachers"]),
                weeks=frozenset(int(week) for week in row["weeks"]),
                sessions=tuple(
                    (
                        int(session["weekday"]),
                        int(session["start_period"]),
                        int(session["end_period"]),
                    )
                    for session in row["sessions"]
                ),
            )
            for row in timetable["courses"]
        )

    @property
    def teachers(self) -> tuple[str, ...]:
        return tuple(sorted({teacher for course in self.courses for teacher in course.teachers}))

    def teaching_week(self, class_date: date) -> int | None:
        week = (class_date - self.start_date).days // 7 + 1
        return week if 1 <= week <= self.total_weeks else None

    def occurrences_for_date(self, class_date: date) -> list[Occurrence]:
        week = self.teaching_week(class_date)
        if week is None:
            return []
        weekday = class_date.isoweekday()
        occurrences: list[Occurrence] = []
        for course in self.courses:
            if week not in course.weeks:
                continue
            for session_weekday, start_period, end_period in course.sessions:
                if session_weekday != weekday:
                    continue
                start_at = datetime.combine(
                    class_date, self.periods[start_period][0], self.timezone
                )
                end_at = datetime.combine(class_date, self.periods[end_period][1], self.timezone)
                occurrences.append(
                    Occurrence(course, class_date, start_period, end_period, start_at, end_at, week)
                )
        return sorted(occurrences, key=lambda occurrence: occurrence.start_at)

    def reminder_due(self, now: datetime) -> list[Occurrence]:
        local_now = now.astimezone(self.timezone)
        return [
            occurrence
            for occurrence in self.occurrences_for_date(local_now.date())
            if occurrence.start_at - timedelta(minutes=self.reminder_minutes)
            <= local_now
            < occurrence.start_at - timedelta(minutes=self.reminder_minutes - 2)
        ]


def load_schedule(data_dir: Path | None = None) -> CourseSchedule:
    directory = data_dir or DATA_DIR
    with (directory / "timetable_2026_fall.yaml").open(encoding="utf-8") as file:
        timetable = yaml.safe_load(file)
    with (directory / "periods_summer.yaml").open(encoding="utf-8") as file:
        periods = yaml.safe_load(file)
    return CourseSchedule(timetable, periods)
