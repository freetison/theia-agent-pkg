import theia_agent.cli as cli


class DummyResult:
    def __init__(self, stdout="", returncode=0):
        self.stdout = stdout
        self.returncode = returncode


def test_run_commit_no_changes_returns_1(monkeypatch, capsys):
    def fake_run(cmd, *args, **kwargs):
        return DummyResult(stdout="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    rc = cli.run_commit(all_repos=False)

    out = capsys.readouterr().out
    assert rc == 1
    assert "No hay cambios" in out


def test_run_commit_success_uses_generated_message(monkeypatch):
    calls = {"argv": None}

    def fake_run(cmd, *args, **kwargs):
        if cmd[:3] == ["git", "diff", "--staged"]:
            return DummyResult(stdout="diff --git a b")
        return DummyResult(stdout="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    monkeypatch.setattr(cli, "_generate_msg", lambda diff: "feat(core): add route")
    monkeypatch.setattr(cli, "run_passthrough", lambda argv: calls.update({"argv": argv}) or 0)
    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    rc = cli.run_commit(all_repos=False)

    assert rc == 0
    assert calls["argv"] == ["git", "super", "--no-verify", "-m", "feat(core): add route"]


def test_run_commit_api_error_returns_1(monkeypatch, capsys):
    def fake_run(cmd, *args, **kwargs):
        if cmd[:3] == ["git", "diff", "--staged"]:
            return DummyResult(stdout="diff --git a b")
        return DummyResult(stdout="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    monkeypatch.setattr(cli, "_generate_msg", lambda diff: None)

    rc = cli.run_commit(all_repos=False)

    out = capsys.readouterr().out
    assert rc == 1
    assert "Error al conectar" in out


def test_run_commit_edit_message_path(monkeypatch):
    calls = {"argv": None}
    answers = iter(["e", "fix(api): adjust timeout"])

    def fake_run(cmd, *args, **kwargs):
        if cmd[:3] == ["git", "diff", "--staged"]:
            return DummyResult(stdout="diff --git a b")
        return DummyResult(stdout="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    monkeypatch.setattr(cli, "_generate_msg", lambda diff: "feat(core): temp")
    monkeypatch.setattr(cli, "run_passthrough", lambda argv: calls.update({"argv": argv}) or 0)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    rc = cli.run_commit(all_repos=False)

    assert rc == 0
    assert calls["argv"] == ["git", "super", "--no-verify", "-m", "fix(api): adjust timeout"]


def test_run_commit_all_uses_status_for_untracked_changes(monkeypatch):
    calls = {"argv": None, "diff_input": None}

    def fake_run(cmd, *args, **kwargs):
        if cmd[:3] == ["git", "diff", "HEAD"]:
            return DummyResult(stdout="")
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return DummyResult(stdout="?? new_file.py\n")
        return DummyResult(stdout="")

    def fake_generate_msg(diff):
        calls["diff_input"] = diff
        return "chore(repo): add untracked files"

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    monkeypatch.setattr(cli, "_generate_msg", fake_generate_msg)
    monkeypatch.setattr(cli, "run_passthrough", lambda argv: calls.update({"argv": argv}) or 0)
    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    rc = cli.run_commit(all_repos=True)

    assert rc == 0
    assert "new file: new_file.py" in calls["diff_input"]
    assert calls["argv"] == ["git", "super", "--all", "--no-verify", "-m", "chore(repo): add untracked files"]


def test_run_commit_all_no_changes_returns_1(monkeypatch, capsys):
    def fake_run(cmd, *args, **kwargs):
        if cmd[:3] == ["git", "diff", "HEAD"]:
            return DummyResult(stdout="")
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return DummyResult(stdout="")
        return DummyResult(stdout="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    rc = cli.run_commit(all_repos=True)

    out = capsys.readouterr().out
    assert rc == 1
    assert "No hay cambios" in out
