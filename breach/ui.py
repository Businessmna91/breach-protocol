"""ANSI terminal presentation. Stdlib only — nothing to pip install."""
from __future__ import annotations

import os
import shutil
import sys

from . import config

_NO_COLOR = bool(os.environ.get("NO_COLOR"))


def _c(code: str) -> str:
    return "" if _NO_COLOR else code


RESET = _c("\033[0m")
DIM = _c("\033[2m")
BOLD = _c("\033[1m")
GREEN = _c("\033[38;5;79m")
AMBER = _c("\033[38;5;214m")
RED = _c("\033[38;5;203m")
BLUE = _c("\033[38;5;75m")
GREY = _c("\033[38;5;245m")
MAGENTA = _c("\033[38;5;176m")


def width() -> int:
    return min(shutil.get_terminal_size((90, 30)).columns, 100)


def clear() -> None:
    if not _NO_COLOR:
        sys.stdout.write("\033[2J\033[H")
    else:
        print("\n" * 3)


def rule(char: str = "─") -> str:
    return GREY + char * width() + RESET


def banner() -> None:
    clear()
    art = r"""
  ██████╗ ██████╗ ███████╗ █████╗  ██████╗██╗  ██╗
  ██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝██║  ██║
  ██████╔╝██████╔╝█████╗  ███████║██║     ███████║
  ██╔══██╗██╔══██╗██╔══╝  ██╔══██║██║     ██╔══██║
  ██████╔╝██║  ██║███████╗██║  ██║╚██████╗██║  ██║
  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝"""
    print(GREEN + art + RESET)
    print(f"  {DIM}P R O T O C O L{RESET}   {GREY}·{RESET}   "
          f"{GREY}live-fire terminal training{RESET}\n")


def bar(value: int, maximum: int, cells: int = 24, color: str = GREEN) -> str:
    filled = max(0, min(cells, round(cells * value / maximum))) if maximum else 0
    return (color + "█" * filled + RESET + GREY + "░" * (cells - filled) + RESET)


def header(progress) -> None:
    lvl = progress.level
    into = progress.xp_into_level
    print(rule("═"))
    print(f" {BOLD}LEVEL {lvl}{RESET}  {bar(into, config.XP_PER_LEVEL, 20, BLUE)}  "
          f"{into}/{config.XP_PER_LEVEL} XP   {GREY}total {progress.xp} XP  ·  "
          f"{len(progress.cleared)}/9 domains cleared{RESET}")
    print(rule("═"))


def integrity_line(hp: int) -> str:
    color = GREEN if hp > 60 else (AMBER if hp > 20 else RED)
    return f" {BOLD}INTEGRITY{RESET} {bar(hp, config.MAX_INTEGRITY, 24, color)} {hp}/100"


def tag(text: str, color: str) -> str:
    return f"{color}[{text}]{RESET}"


def wrap(text: str, indent: str = "   ") -> str:
    import textwrap
    return "\n".join(textwrap.fill(line, width() - len(indent) - 2,
                                   initial_indent=indent, subsequent_indent=indent)
                     for line in text.split("\n"))


def ask(prompt: str) -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return ":quit"


def pause(msg: str = "press Enter to continue") -> None:
    ask(f"\n{GREY}   {msg}{RESET} ")
