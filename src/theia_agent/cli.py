#!/usr/bin/env python3
"""
theia - pass-through agent CLI with autocomplete / CLI de agentes con autocompletado

ES: / muestra lista de agentes disponibles.
EN: / shows available agents list.
ES: @ abre selector de rutas del filesystem (como Claude Code).
EN: @ opens filesystem path selector (like Claude Code).
"""

import sys
import os
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

# ES: prompt_toolkit para autocompletado | EN: prompt_toolkit for autocomplete
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
    from prompt_toolkit.formatted_text import HTML
    HAS_PROMPT = True
except ImportError:
    HAS_PROMPT = False

# ES: tabla de ruteo | EN: routing table
ROUTES = {
    # ES: Claude Code -> .claude/agents/<agent>.md | EN: Claude Code -> .claude/agents/<agent>.md
    "cto":        {"cli": "claude",  "agent": "cto",       "desc": "CTO — planificación y prioridades"},
    "architect":  {"cli": "claude",  "agent": "architect", "desc": "Arquitecto — diseño y ADRs"},
    "plan":       {"cli": "claude",  "agent": "cto",       "desc": "Planificación (alias cto)"},
    "context":    {"cli": "claude",  "agent": "architect", "desc": "Contexto de arquitectura"},
    "security":   {"cli": "claude",  "agent": "security",  "desc": "Revisión de seguridad"},
    "devops":     {"cli": "claude",  "agent": "devops",    "desc": "DevOps — infra, CI/CD"},
    "tester":     {"cli": "claude",  "agent": "tester",    "desc": "Tests — cobertura >= 90%"},
    "reviewer":   {"cli": "claude",  "agent": "reviewer",  "desc": "Code review"},
    "backend":    {"cli": "claude",  "agent": "backend",   "desc": "Backend — APIs, servicios"},

    # ES: Copilot CLI -> .github/copilot/agents/<agent>.agent.md | EN: Copilot CLI -> .github/copilot/agents/<agent>.agent.md
    "co-backend":  {"cli": "copilot", "agent": "backend",  "desc": "Copilot backend (operacional)"},
    "co-frontend": {"cli": "copilot", "agent": "frontend", "desc": "Copilot frontend (operacional)"},
    "co-devops":   {"cli": "copilot", "agent": "devops",   "desc": "Copilot DevOps (operacional)"},
    "co-test":     {"cli": "copilot", "agent": "tester",   "desc": "Copilot tester (operacional)"},
    "co-review":   {"cli": "copilot", "agent": "reviewer", "desc": "Copilot reviewer (operacional)"},

    # ES: commits con GPT-4o via GitHub Copilot API -> git super | EN: commits via GPT-4o and GitHub Copilot API -> git super
    "commit":     {"cli": "commit", "agent": None,  "desc": "staged diff → GPT-4o → git super --no-verify"},
    "commit-all": {"cli": "commit", "agent": "all", "desc": "full diff   → GPT-4o → git super --all --no-verify"},
}

SLASH_COMMANDS = list(ROUTES.keys()) + ["list", "exit"]

CLAUDE_COMMANDS  = [k for k, v in ROUTES.items() if v["cli"] == "claude"]
COPILOT_COMMANDS = [k for k, v in ROUTES.items() if v["cli"] == "copilot"]
COMMIT_COMMANDS  = [k for k, v in ROUTES.items() if v["cli"] == "commit"]

# ES: autocompletado | EN: autocomplete

class TheiaCompleter(Completer):
    """
    ES: / completa nombres de agentes y descripcion.
    EN: / completes agent names and description.
    ES: @ completa rutas del filesystem desde cwd.
    EN: @ completes filesystem paths from cwd.
    """

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # ES: completado de archivos con @ | EN: @ file completion
        at_pos = text.rfind("@")
        if at_pos != -1:
            partial = text[at_pos + 1:]
            # ES: sin espacios tras @ significa que sigue escribiendo ruta | EN: no spaces after @ means user is still typing the path
            if " " not in partial:
                yield from self._file_completions(partial)
                return

        # ES: completado de slash-commands | EN: slash-command completion
        slash_pos = text.rfind("/")
        if slash_pos != -1:
            before_slash = text[:slash_pos].strip()
            # ES: completar solo si / inicia token y no es parte de ruta | EN: complete only when / starts a token, not a path segment
            if not before_slash or before_slash.endswith(" "):
                partial = text[slash_pos + 1:]
                # ES: sin espacios significa que sigue escribiendo comando | EN: no spaces means user is still typing the command
                if " " not in partial:
                    yield from self._slash_completions(partial)
                    return

    def _slash_completions(self, partial: str):
        partial_lower = partial.lower()
        for cmd in SLASH_COMMANDS:
            if cmd.startswith(partial_lower):
                info = ROUTES.get(cmd, {})
                desc = info.get("desc", "")
                cli  = info.get("cli", "")

                # ES: etiqueta visual por tipo de comando | EN: visual badge by command type
                if cli == "claude":
                    badge = "🤖 claude"
                elif cli == "copilot":
                    badge = "💻 copilot"
                elif cli == "commit":
                    badge = "📦 commit"
                else:
                    badge = ""

                display_meta = f"{badge}  {desc}" if desc else badge

                yield Completion(
                    text=cmd,
                    start_position=-len(partial),
                    display=f"/{cmd}",
                    display_meta=display_meta,
                )

    def _file_completions(self, partial: str):
        cwd = Path(os.getcwd())

        # ES: separar directorio base y fragmento final | EN: split base directory and final fragment
        if "/" in partial or "\\" in partial:
            base = Path(partial).parent
            frag = Path(partial).name
        else:
            base = Path(".")
            frag = partial

        search_dir = (cwd / base).resolve()

        try:
            entries = sorted(search_dir.iterdir(), key=lambda p: (p.is_file(), p.name))
        except (PermissionError, FileNotFoundError):
            return

        for entry in entries:
            if entry.name.startswith(".") and not frag.startswith("."):
                continue  # ES: ocultar dotfiles salvo que el usuario los pida | EN: hide dotfiles unless explicitly requested
            if entry.name.lower().startswith(frag.lower()):
                suffix = "/" if entry.is_dir() else ""
                rel = str(entry.relative_to(cwd)).replace("\\", "/")
                yield Completion(
                    text=rel + suffix,
                    start_position=-len(partial),
                    display=entry.name + suffix,
                    display_meta="dir" if entry.is_dir() else entry.suffix or "file",
                )


# ES: commit helper via Copilot API con GPT-4o | EN: commit helper via Copilot API with GPT-4o

COMMIT_SYSTEM = (
    "You are an expert at writing git commit messages following the Conventional Commits spec.\n"
    "Given a git diff, write ONE commit message.\n"
    "Format: <type>(<scope>): <subject>\n"
    "Types: feat, fix, refactor, chore, docs, test, style, perf, build, ci\n"
    "Subject: imperative mood, max 72 chars, no period at end.\n"
    "Output ONLY the commit message — no explanation, no markdown, no quotes."
)

def _gh_token() -> str | None:
    try:
        r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
        t = r.stdout.strip()
        return t if t else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

def _copilot_session_token(gh_token: str) -> str | None:
    req = urllib.request.Request(
        "https://api.github.com/copilot_internal/v2/token",
        headers={
            "Authorization": f"token {gh_token}",
            "Accept": "application/json",
            "Editor-Version": "theia-agent/0.1",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("token")
    except Exception:
        return None

def _generate_msg(diff: str) -> str | None:
    gh_token = _gh_token()
    if not gh_token:
        return None
    session_token = _copilot_session_token(gh_token)
    if not session_token:
        return None

    diff_body = diff[:6000] + ("\n[...truncated...]" if len(diff) > 6000 else "")
    payload = json.dumps({
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": COMMIT_SYSTEM},
            {"role": "user",   "content": f"diff:\n{diff_body}"},
        ],
        "max_tokens": 100,
        "temperature": 0.2,
    }).encode()

    req = urllib.request.Request(
        "https://api.githubcopilot.com/chat/completions",
        data=payload,
        headers={
            "Authorization":          f"Bearer {session_token}",
            "Content-Type":           "application/json",
            "Copilot-Integration-Id": "theia-agent",
            "Editor-Version":         "theia-agent/0.1",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None

def run_commit(all_repos: bool = False) -> int:
    cwd = os.getcwd()
    diff_cmd = ["git", "diff", "HEAD"] if all_repos else ["git", "diff", "--staged"]
    diff = subprocess.run(diff_cmd, capture_output=True, text=True, cwd=cwd).stdout.strip()
    if not diff and not all_repos:
        diff = subprocess.run(["git", "diff"], capture_output=True, text=True, cwd=cwd).stdout.strip()
    if not diff:
        print("  [theia] No hay cambios para commitear.")
        return 1

    print("  [theia] Generando mensaje con GPT-4o...", end="", flush=True)
    msg = _generate_msg(diff)
    if not msg:
        print(" ✗")
        print("  [theia] Error al conectar con Copilot API. Comprueba: gh auth status")
        return 1

    print(" ✓")
    print(f"\n  {msg}\n")

    try:
        answer = input("  ¿Usar este mensaje? [Y/n/e=editar] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(); return 130

    if answer in ("n", "no"):
        print("  Cancelado."); return 0

    if answer in ("e", "edit", "editar"):
        try:
            msg = input("  Mensaje: ").strip()
            if not msg:
                print("  Cancelado."); return 0
        except (EOFError, KeyboardInterrupt):
            print(); return 130

    cmd = ["git", "super", "--all", "--no-verify", "-m", msg] if all_repos \
     else ["git", "super",          "--no-verify", "-m", msg]
    return run_passthrough(cmd)

# ES: pass-through generico | EN: generic pass-through

def build_command(cmd: str, prompt: str) -> list[str]:
    route = ROUTES[cmd]
    if route["cli"] == "claude":
        return ["claude", "--agent", route["agent"], "-p", prompt] if prompt \
          else ["claude", "--agent", route["agent"]]
    else:
        return ["gh", "copilot", "suggest", "-t", "shell", prompt] if prompt \
          else ["gh", "copilot", "suggest", "-t", "shell"]

def run_passthrough(argv: list[str]) -> int:
    try:
        return subprocess.run(argv, cwd=os.getcwd()).returncode
    except FileNotFoundError:
        hints = {
            "claude": "https://docs.anthropic.com/claude-code",
            "gh":     "https://cli.github.com/ → gh extension install github/gh-copilot",
            "git":    "https://git-scm.com/",
        }
        print(f"\n  [theia] No encontrado: {argv[0]}", file=sys.stderr)
        if argv[0] in hints:
            print(f"  {hints[argv[0]]}", file=sys.stderr)
        return 127
    except KeyboardInterrupt:
        return 130

# ES: ayuda | EN: help

def print_help():
    print()
    print("  theia — agent router")
    print()
    print("  Claude Code (estratégicos):")
    for c in CLAUDE_COMMANDS:
        print(f"    /{c:<14}  {ROUTES[c]['desc']}")
    print()
    print("  Copilot CLI (operacionales):")
    for c in COPILOT_COMMANDS:
        print(f"    /{c:<14}  {ROUTES[c]['desc']}")
    print()
    print("  Commits — GPT-4o via Copilot → git super:")
    print(f"    /commit         {ROUTES['commit']['desc']}")
    print(f"    /commit-all     {ROUTES['commit-all']['desc']}")
    print()
    print("  Autocompletado:")
    print("    /   →  lista de agentes")
    print("    @   →  selector de rutas del filesystem")
    print()
    print("  /list · /exit")
    print()

# ES: despachador de comandos | EN: command dispatcher

def dispatch(cmd: str, prompt: str) -> int:
    if cmd in ("list", "help", "?"):
        print_help(); return 0
    if cmd in ("exit", "quit", "q"):
        return -1
    if cmd == "commit":
        return run_commit(all_repos=False)
    if cmd == "commit-all":
        return run_commit(all_repos=True)
    if cmd not in ROUTES:
        print(f"  Desconocido: /{cmd}"); print_help(); return 1
    return run_passthrough(build_command(cmd, prompt))

def parse_line(line: str) -> tuple[str | None, str]:
    line = line.strip()
    if not line.startswith("/"):
        return None, line
    parts = line[1:].split(None, 1)
    return parts[0].lower(), (parts[1] if len(parts) > 1 else "")

# ES: REPL interactivo | EN: interactive REPL

def repl():
    print("\n  theia  /comando [mensaje @archivo]  —  /list\n")

    if HAS_PROMPT:
        history_file = Path.home() / ".theia_history"
        session = PromptSession(
            history=FileHistory(str(history_file)),
            completer=TheiaCompleter(),
            complete_while_typing=True,
            style=Style.from_dict({
                "prompt":      "ansigreen bold",
                "completion-menu.completion":          "bg:#1e1e2e fg:#cdd6f4",
                "completion-menu.completion.current":  "bg:#89b4fa fg:#1e1e2e bold",
                "completion-menu.meta.completion":     "bg:#1e1e2e fg:#6c7086",
                "completion-menu.meta.completion.current": "bg:#89b4fa fg:#1e1e2e",
            }),
        )
        prompt_fn = lambda: session.prompt(HTML("<prompt>theia</prompt> › "))
    else:
        # ES: fallback si prompt_toolkit no esta disponible | EN: fallback when prompt_toolkit is unavailable
        prompt_fn = lambda: input("theia › ")

    while True:
        try:
            line = prompt_fn().strip()
        except (EOFError, KeyboardInterrupt):
            print(); break

        if not line:
            continue

        cmd, prompt = parse_line(line)
        if cmd is None:
            print("  Usa /comando — escribe /list o pulsa / + Tab")
            continue
        if dispatch(cmd, prompt) == -1:
            break
        print()

# ES: punto de entrada | EN: entry point

def main():
    args = sys.argv[1:]
    if not args:
        repl(); return
    if args[0] in ("/list", "--list", "-l", "/help"):
        print_help(); return
    if args[0].startswith("/"):
        cmd = args[0][1:].lower()
        prompt = " ".join(args[1:])
        rc = dispatch(cmd, prompt)
        sys.exit(0 if rc == -1 else rc)
    print("  Uso: theia /comando [mensaje]", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()