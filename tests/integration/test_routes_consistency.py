import theia_agent.cli as cli
import theia_agent.server as server


def test_routes_are_kept_in_sync_between_cli_and_mcp():
    assert cli.ROUTES == server.ROUTES
