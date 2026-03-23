import theia_agent.cli as cli
from pathlib import Path


class DummyResult:
    def __init__(self, returncode):
        self.returncode = returncode


def test_build_command_claude_with_prompt():
    argv = cli.build_command("cto", "plan")
    assert argv == ["claude", "--agent", "cto", "plan"]


def test_build_command_copilot_without_prompt():
    argv = cli.build_command("co-backend", "")
    assert argv == ["gh", "copilot", "--", "--continue"]


def test_build_command_copilot_with_prompt():
    argv = cli.build_command("co-backend", "revise this module")
    assert argv == ["gh", "copilot", "--", "-i", "revise this module"]


def test_build_command_claude_with_at_path_adds_add_dir(monkeypatch, tmp_path):
    tools_dir = tmp_path / "theia-dev-tools"
    tools_dir.mkdir()
    compose = tools_dir / "docker-compose.yml"
    compose.write_text("services: {}", encoding="utf-8")

    monkeypatch.setattr(cli.os, "getcwd", lambda: str(tmp_path))

    argv = cli.build_command("devops", "revisa @theia-dev-tools/docker-compose.yml")

    assert argv[0:3] == ["claude", "--agent", "devops"]
    assert "--add-dir" in argv
    idx = argv.index("--add-dir")
    assert Path(argv[idx + 1]) == tools_dir.resolve()


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
