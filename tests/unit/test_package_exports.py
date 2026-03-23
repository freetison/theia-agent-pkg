import theia_agent as pkg


def test_public_exports_are_available():
    assert callable(pkg.cli_main)
    assert callable(pkg.mcp_main)
    assert isinstance(pkg.ROUTES, dict)
    assert callable(pkg.run_passthrough)


def test_all_contains_expected_symbols():
    expected = {"cli_main", "mcp_main", "mcp", "ROUTES", "run_passthrough"}
    assert expected.issubset(set(pkg.__all__))
