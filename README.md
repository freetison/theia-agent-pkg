# theia-agent

Pass-through CLI/MCP router for Claude Code and GitHub Copilot agents.
Router CLI/MCP de pass-through para agentes de Claude Code y GitHub Copilot.

## Features / Caracteristicas

- Slash-command router for strategy and operational agents.
- Enrutador por slash-commands para agentes estrategicos y operativos.
- Interactive CLI with command and file completion.
- CLI interactiva con autocompletado de comandos y archivos.
- MCP server for editor/tool integrations.
- Servidor MCP para integraciones con editor/herramientas.
- Commit message generator via Copilot API (`/commit`, `/commit-all`).
- Generador de mensajes de commit via API de Copilot (`/commit`, `/commit-all`).

## Requirements / Requisitos

- Python 3.11+
- `claude` CLI installed for Claude routes.
- `gh` CLI + `gh extension install github/gh-copilot` for Copilot routes.
- `git` and `git super` command available for commit flows.
- Authenticated GitHub CLI session (`gh auth login`).

## Install / Instalacion

```bash
pip install -e .
```

With test deps / Con dependencias de test:

```bash
pip install -e .[test]
```

## Usage / Uso

List commands / Listar comandos:

```bash
theia --list
```

Interactive mode / Modo interactivo:

```bash
theia
```

Direct command / Comando directo:

```bash
theia /cto Plan sprint y prioridades
```

Commit helper / Asistente de commit:

```bash
theia /commit
theia /commit-all
```

## MCP Server

Run server / Ejecutar servidor:

```bash
theia-mcp
```

Exposed tools / Herramientas expuestas:

- `resolve(command)`
- `list_routes()`

## Development / Desarrollo

Run tests / Ejecutar tests:

```bash
pytest -q
```

Coverage gate (>=80%) / Umbral de cobertura (>=80%):

```bash
pytest --cov=src/theia_agent --cov-report=term-missing --cov-fail-under=80
```

## Troubleshooting

- If `/commit` fails, verify `gh auth status` and network access.
- Si falla `/commit`, verifica `gh auth status` y acceso a red.
- If `claude` or `gh` is missing, install required CLIs and retry.
- Si falta `claude` o `gh`, instala las CLIs requeridas y reintenta.

## Notes / Notas

- The router forwards commands; target CLIs execute real work.
- El router reenvia comandos; las CLIs objetivo ejecutan el trabajo real.
- `ROUTES` is currently duplicated in CLI and MCP modules and validated by tests.
- `ROUTES` esta duplicado actualmente entre modulos CLI y MCP y se valida con tests.
