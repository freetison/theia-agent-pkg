__version__ = "0.1.0"

from .cli import main as cli_main, ROUTES, run_passthrough
from .server import mcp, main as mcp_main


# ES: anadir un agente custom en tiempo de ejecucion | EN: add a custom agent at runtime
# from theia_agent import ROUTES, run_passthrough
# ROUTES["dba"] = {"cli": "claude", "agent": "dba"}

__all__ = [
    "cli_main",
    "mcp_main",
    "mcp",
    "ROUTES",
    "run_passthrough",
]