import theia_agent.server as server


def test_resolve_found_normalizes_case_and_slash():
    result = server.resolve("/CTO")

    assert result["found"] is True
    assert result["command"] == "cto"
    assert result["cli"] == "claude"


def test_resolve_not_found_returns_available_list():
    result = server.resolve("/does-not-exist")

    assert result["found"] is False
    assert result["command"] == "does-not-exist"
    assert "available" in result
    assert "cto" in result["available"]


def test_list_routes_has_expected_shape():
    routes = server.list_routes()

    assert isinstance(routes, list)
    assert routes
    first = routes[0]
    assert first["command"].startswith("/")
    assert "cli" in first
    assert "desc" in first
