from plugins.kirakira.commands import is_group_admin, parse_cf_arguments, valid_handle


def test_parse_cf_arguments() -> None:
    assert parse_cf_arguments("cf tourist", 2) == ["cf", "tourist"]
    assert parse_cf_arguments("CF", 1) == ["CF"]
    assert parse_cf_arguments("cf tourist extra", 2) is None


def test_handle_validation() -> None:
    assert valid_handle("tourist_1")
    assert valid_handle("a-b")
    assert not valid_handle("bad handle")
    assert not valid_handle("bad/")


def test_group_admin_role() -> None:
    assert is_group_admin("admin")
    assert is_group_admin("owner")
    assert not is_group_admin("member")
