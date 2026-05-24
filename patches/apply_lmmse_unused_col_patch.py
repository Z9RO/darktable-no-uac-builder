#!/usr/bin/env python3
"""
Patch darktable's lmmse.c to remove an unused loop variable.

GCC 15 reports the lmmse.c inner-loop "col" induction variable as set but
unused. darktable builds with -Werror, so this warning fails the Windows build.

Usage:
    python apply_lmmse_unused_col_patch.py <path/to/lmmse.c>
"""

from pathlib import Path
import re
import sys


def apply_lmmse_unused_col_patch(lmmse_path: str) -> None:
    """Remove the unused lmmse.c col loop variable if it is present."""

    path = Path(lmmse_path)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8")

    # Match the loop header that declares and increments the unused variable:
    #   for(int ccc = BORDER_AROUND, col = colStart;
    #       ccc < tileCols + BORDER_AROUND;
    #       ccc++, col++, cfa++, idx++)
    pattern = re.compile(
        r"(for\(int ccc = BORDER_AROUND),\s*col = colStart;"
        r"(\n\s*ccc < tileCols \+ BORDER_AROUND;"
        r"\n\s*ccc\+\+),\s*col\+\+(,\s*cfa\+\+,\s*idx\+\+\))"
    )
    patched_pattern = re.compile(
        r"for\(int ccc = BORDER_AROUND;"
        r"\n\s*ccc < tileCols \+ BORDER_AROUND;"
        r"\n\s*ccc\+\+,\s*cfa\+\+,\s*idx\+\+\)"
    )

    matches = pattern.findall(content)
    if len(matches) == 1:
        path.write_text(pattern.sub(r"\1;\2\3", content, count=1), encoding="utf-8")
        print(f"Patched unused loop variable in: {path}")
    elif len(matches) > 1:
        print(
            "ERROR: found multiple lmmse loop patterns; refusing to patch "
            "ambiguously.",
            file=sys.stderr,
        )
        sys.exit(1)
    elif patched_pattern.search(content):
        print(f"lmmse unused loop variable already patched in: {path}")
    else:
        print(
            "ERROR: expected lmmse loop pattern was not found; "
            "upstream source may have changed.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/lmmse.c>", file=sys.stderr)
        sys.exit(1)

    apply_lmmse_unused_col_patch(sys.argv[1])
