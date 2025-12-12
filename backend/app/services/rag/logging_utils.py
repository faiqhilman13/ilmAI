"""Utilities for structured, readable RAG logs."""

from __future__ import annotations

import os
import sys
import textwrap
from typing import Iterable, List, Optional

_MAX_WIDTH = 100
_MIN_WIDTH = 40


def _supports_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    stream = sys.stderr
    return hasattr(stream, "isatty") and stream.isatty()


_USE_COLOR = _supports_color()
_COLORS = {
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "magenta": "\033[35m",
    "red": "\033[31m",
    "blue": "\033[34m",
}
_RESET = "\033[0m"


def format_box(
    title: str, lines: Iterable[str] | str, color: Optional[str] = None
) -> str:
    if isinstance(lines, str):
        raw_lines: List[str] = [lines]
    else:
        raw_lines = [str(l) for l in lines]

    wrapped: List[str] = []
    for line in raw_lines:
        for part in str(line).splitlines() or [""]:
            if len(part) <= _MAX_WIDTH:
                wrapped.append(part)
            else:
                wrapped.extend(textwrap.wrap(part, width=_MAX_WIDTH))

    content_width = max([len(title)] + [len(l) for l in wrapped]) + 4
    width = max(_MIN_WIDTH, min(content_width, _MAX_WIDTH + 4))

    top = "┌" + "─" * (width - 2) + "┐"
    title_line = "│ " + title.center(width - 4) + " │"
    sep = "├" + "─" * (width - 2) + "┤"
    body_lines = ["│ " + l.ljust(width - 4) + " │" for l in wrapped]
    bottom = "└" + "─" * (width - 2) + "┘"

    box = "\n".join([top, title_line, sep, *body_lines, bottom])
    if _USE_COLOR and color:
        code = _COLORS.get(color)
        if code:
            return code + box + _RESET
    return box

