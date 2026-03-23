import json

import pytest

import theia_agent.cli as cli


class DummyRunResult:
    def __init__(self, stdout="", returncode=0):
        self.stdout = stdout
        self.returncode = returncode


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._payload).encode()


def test_gh_token_success(monkeypatch):
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *args, **kwargs: DummyRunResult(stdout="token-123\n"),
    )

    assert cli._gh_token() == "token-123"


def test_gh_token_missing_binary(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert cli._gh_token() is None


def test_copilot_session_token_success(monkeypatch):
    monkeypatch.setattr(
        cli.urllib.request,
        "urlopen",
        lambda req, timeout=10: DummyResponse({"token": "session-abc"}),
    )

    assert cli._copilot_session_token("gh-token") == "session-abc"


def test_generate_msg_success(monkeypatch):
    monkeypatch.setattr(cli, "_gh_token", lambda: "gh-token")
    monkeypatch.setattr(cli, "_copilot_session_token", lambda token: "session-token")

    payload = {
        "choices": [{"message": {"content": "feat(core): add tests"}}],
    }
    monkeypatch.setattr(
        cli.urllib.request,
        "urlopen",
        lambda req, timeout=20: DummyResponse(payload),
    )

    assert cli._generate_msg("diff --git a b") == "feat(core): add tests"


def test_generate_msg_returns_none_without_tokens(monkeypatch):
    monkeypatch.setattr(cli, "_gh_token", lambda: None)
    assert cli._generate_msg("diff") is None


def test_print_help_contains_sections(capsys):
    cli.print_help()
    out = capsys.readouterr().out

    assert "theia — agent router" in out
    assert "/commit" in out


def test_repl_fallback_exits_on_exit(monkeypatch):
    answers = iter(["/exit"])

    monkeypatch.setattr(cli, "HAS_PROMPT", False)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    cli.repl()


def test_main_without_args_calls_repl(monkeypatch):
    called = {"repl": False}

    monkeypatch.setattr(cli, "repl", lambda: called.update({"repl": True}))
    monkeypatch.setattr(cli.sys, "argv", ["theia"])

    cli.main()

    assert called["repl"] is True


def test_main_with_slash_command_exits_with_dispatch_code(monkeypatch):
    monkeypatch.setattr(cli.sys, "argv", ["theia", "/cto", "ship"])
    monkeypatch.setattr(cli, "dispatch", lambda cmd, prompt: 3)

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 3


def test_main_with_invalid_usage_exits_1(monkeypatch):
    monkeypatch.setattr(cli.sys, "argv", ["theia", "invalid"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 1


def test_read_repl_input_single_line():
    prompt_calls = iter(["/devops hola"])
    line = cli._read_repl_input(lambda: next(prompt_calls), lambda: "")
    assert line == "/devops hola"


def test_read_repl_input_multiline_with_trailing_backslash():
    prompt_calls = iter(["/devops linea 1\\", "linea 2"])
    line = cli._read_repl_input(lambda: next(prompt_calls), lambda: next(prompt_calls))
    assert line == "/devops linea 1\nlinea 2"
