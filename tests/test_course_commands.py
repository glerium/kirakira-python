from plugins.kirakira.course_commands import parse_subscription_args


def test_parse_subscription_args() -> None:
    assert parse_subscription_args("class all", 2) == ["class", "all"]
    assert parse_subscription_args("class 刘娟", 2) == ["class", "刘娟"]
    assert parse_subscription_args("class", 2) is None
