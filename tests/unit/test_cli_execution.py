import theia_agent.cli as cli


class DummyResult:
    def __init__(self, returncode):
        self.returncode = returncode


def test_build_command_claude_with_prompt():
    argv = cli.build_command("cto", "plan")
    assert argv == ["claude", "--agent", "cto", "-p", "plan"]


def test_build_command_copilot_without_prompt():
    argv = cli.build_command("co-backend", "")
    assert argv == ["gh", "copilot", "suggest", "-t", "shell"]


def test_run_passthrough_success(monkeypatch):
    monkeypatch.setattr(cli.subprocess, "run", lambda *args, **kwargs: DummyResult(0))
    rc = cli.run_passthrough(["anything"])
    assert rc == 0


def test_run_passthrough_missing_binary(monkeypatch, capsys):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    rc = cli.run_passthrough(["gh"])

    err = capsys.readouterr().err
    assert rc == 127
    assert "No encontrado" in err


def test_run_passthrough_ctrl_c(monkeypatch):
    def fake_run(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert cli.run_passthrough(["any"]) == 130
