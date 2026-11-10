"""Tests for the local .env reader."""

from pathlib import Path

from kaggle_scout.env_file import load_env_file, read_env_file


def test_read_env_file_parses_pairs_comments_and_quotes(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "# comment\n"
        "\n"
        "PLAIN=value\n"
        'DOUBLE="quoted value"\n'
        "SINGLE='single'\n"
        "export EXPORTED=yes\n"
        "EMPTY=\n"
        "WITH_EQUALS=a=b\n"
        "not a pair\n",
        encoding="utf-8",
    )

    assert read_env_file(path) == {
        "PLAIN": "value",
        "DOUBLE": "quoted value",
        "SINGLE": "single",
        "EXPORTED": "yes",
        "EMPTY": "",
        "WITH_EQUALS": "a=b",
    }


def test_read_env_file_returns_empty_dict_when_missing(tmp_path: Path) -> None:
    assert read_env_file(tmp_path / "missing.env") == {}


def test_load_env_file_does_not_override_existing_values(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("KEEP=file\nNEW=file\n", encoding="utf-8")
    environ = {"KEEP": "existing"}

    load_env_file(path, environ)

    assert environ == {"KEEP": "existing", "NEW": "file"}
