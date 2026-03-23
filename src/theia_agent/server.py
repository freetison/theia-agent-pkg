"""
theia-agent MCP server / servidor MCP de theia-agent
ES: solo sabe a que comando mapea cada /slash-command.
EN: it only knows which command each /slash-command maps to.
ES: el cliente es quien ejecuta; pass-through puro.
EN: the client executes; pure pass-through.
"""

from fastmcp import FastMCP

mcp = FastMCP(
    name="theia-agent-router",
    instructions=(
        "ES: devuelve el comando exacto a ejecutar para cada agente. "
        "EN: returns the exact command to execute for each agent. "
        "ES: el cliente hace el pass-through. EN: the client performs pass-through."
    )
)

# ES: tabla de ruteo | EN: routing table
# ES: fuente de verdad de agentes, carpetas y CLI | EN: source of truth for agents, folders, and CLI

ROUTES = {
    # ES: agentes de Claude Code -> claude --agent <n> | EN: Claude Code agents -> claude --agent <n>
    # ES: archivos en .claude/agents/<n>.md | EN: files live in .claude/agents/<n>.md
    "cto":        {"cli": "claude", "agent": "cto",        "desc": "CTO — planificación y prioridades"},
    "architect":  {"cli": "claude", "agent": "architect",  "desc": "Arquitecto — diseño y ADRs"},
    "plan":       {"cli": "claude", "agent": "cto",        "desc": "Planificación (alias cto)"},
    "context":    {"cli": "claude", "agent": "architect",  "desc": "Contexto de arquitectura"},
    "security":   {"cli": "claude", "agent": "security",   "desc": "Revisión de seguridad"},
    "devops":     {"cli": "claude", "agent": "devops",     "desc": "DevOps — infra, CI/CD"},
    "tester":     {"cli": "claude", "agent": "tester",     "desc": "Tests — cobertura >= 90%"},
    "reviewer":   {"cli": "claude", "agent": "reviewer",   "desc": "Code review"},
    "backend":    {"cli": "claude", "agent": "backend",    "desc": "Backend — APIs, servicios"},

    # ES: agentes de Copilot -> gh copilot suggest | EN: Copilot agents -> gh copilot suggest
    # ES: archivos en .github/copilot/agents/<n>.agent.md | EN: files live in .github/copilot/agents/<n>.agent.md
    "co-backend":  {"cli": "copilot", "agent": "backend",  "desc": "Copilot backend (operacional)"},
    "co-frontend": {"cli": "copilot", "agent": "frontend", "desc": "Copilot frontend (operacional)"},
    "co-devops":   {"cli": "copilot", "agent": "devops",   "desc": "Copilot DevOps (operacional)"},
    "co-test":     {"cli": "copilot", "agent": "tester",   "desc": "Copilot tester (operacional)"},
    "co-review":   {"cli": "copilot", "agent": "reviewer", "desc": "Copilot reviewer (operacional)"},

    # ES: commits con GPT-4o via Copilot API -> git super | EN: commits via GPT-4o and Copilot API -> git super
    "commit":     {"cli": "commit", "agent": None,  "desc": "staged diff → GPT-4o → git super --no-verify"},
    "commit-all": {"cli": "commit", "agent": "all", "desc": "full diff   → GPT-4o → git super --all --no-verify"},
}


@mcp.tool()
def resolve(command: str) -> dict:
    """
    ES: dado un slash-command, devuelve el CLI y agente a usar.
    EN: given a slash-command, returns the CLI and agent to use.

    Returns:
        {
            "cli":   "claude" | "copilot",
            "agent": "<agent-name>",
            "desc":  "<descripcion/description>",
            "found": true | false
        }
    """
    cmd = command.lower().lstrip("/")
    if cmd in ROUTES:
        return {**ROUTES[cmd], "found": True, "command": cmd}
    return {
        "found": False,
        "command": cmd,
        "available": list(ROUTES.keys()),
    }


@mcp.tool()
def list_routes() -> list:
    """ES: lista comandos disponibles con CLI y descripcion. EN: list all available commands with CLI and description."""
    return [
        {"command": f"/{cmd}", **info}
        for cmd, info in ROUTES.items()
    ]


def main():
    mcp.run()


if __name__ == "__main__":
    main()
    mcp.run()