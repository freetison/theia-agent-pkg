from pathlib import Path

import theia_agent.cli as cli


class DummyDoc:
    def __init__(self, text_before_cursor):
        self.text_before_cursor = text_before_cursor


def test_slash_completions_match_prefix():
    completer = cli.TheiaCompleter()
    items = list(completer._slash_completions("co"))
    texts = {item.text for item in items}

    assert "co-backend" in texts
    assert "co-review" in texts


def test_get_completions_uses_slash_mode():
    completer = cli.TheiaCompleter()
    items = list(completer.get_completions(DummyDoc("/ct"), None))
    texts = {item.text for item in items}

    assert "cto" in texts


def test_file_completions_hide_dotfiles_by_default(monkeypatch, tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".git").mkdir()

    monkeypatch.setattr(cli.os, "getcwd", lambda: str(tmp_path))

    completer = cli.TheiaCompleter()
    items = list(completer._file_completions(""))
    displays = {item.display_text for item in items}

    assert "src/" in displays
    assert ".git/" not in displays


def test_file_completions_show_dotfiles_when_requested(monkeypatch, tmp_path):
    (tmp_path / ".github").mkdir()

    monkeypatch.setattr(cli.os, "getcwd", lambda: str(tmp_path))

    completer = cli.TheiaCompleter()
    items = list(completer._file_completions("."))
    displays = {item.display_text for item in items}

    assert ".github/" in displays


def test_file_completions_nonexistent_dir_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.os, "getcwd", lambda: str(tmp_path))

    completer = cli.TheiaCompleter()
    items = list(completer._file_completions("missing/path"))

    assert items == []


def test_file_completions_support_backslash_separator(monkeypatch, tmp_path):
    (tmp_path / "theia-dev-tools").mkdir()
    (tmp_path / "theia-dev-tools" / "docker-compose.yml").write_text("services: {}", encoding="utf-8")

    monkeypatch.setattr(cli.os, "getcwd", lambda: str(tmp_path))

    completer = cli.TheiaCompleter()
    items = list(completer._file_completions("theia-dev-tools\\"))
    displays = {item.display_text for item in items}

    assert "docker-compose.yml" in displays
