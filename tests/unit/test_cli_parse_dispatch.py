import theia_agent.cli as cli


def test_parse_line_command_and_prompt():
    cmd, prompt = cli.parse_line("/cto build api")
    assert cmd == "cto"
    assert prompt == "build api"


def test_parse_line_plain_text_returns_none_command():
    cmd, prompt = cli.parse_line("hola mundo")
    assert cmd is None
    assert prompt == "hola mundo"


def test_dispatch_list_calls_help(monkeypatch):
    called = {"help": False}

    def fake_help():
        called["help"] = True

    monkeypatch.setattr(cli, "print_help", fake_help)
    rc = cli.dispatch("list", "")

    assert rc == 0
    assert called["help"] is True


def test_dispatch_exit_returns_minus_one():
    assert cli.dispatch("exit", "") == -1


def test_dispatch_commit_routes_to_run_commit(monkeypatch):
    called = {"all_repos": None}

    def fake_run_commit(*, all_repos):
        called["all_repos"] = all_repos
        return 0

    monkeypatch.setattr(cli, "run_commit", fake_run_commit)

    rc = cli.dispatch("commit", "")

    assert rc == 0
    assert called["all_repos"] is False


def test_dispatch_unknown_returns_error(capsys):
    rc = cli.dispatch("unknown-cmd", "")

    out = capsys.readouterr().out
    assert rc == 1
    assert "Desconocido" in out


def test_dispatch_known_calls_passthrough(monkeypatch):
    monkeypatch.setattr(cli, "build_command", lambda cmd, prompt: ["dummy", cmd, prompt])
    monkeypatch.setattr(cli, "run_passthrough", lambda argv: 7)

    rc = cli.dispatch("cto", "ship it")

    assert rc == 7
