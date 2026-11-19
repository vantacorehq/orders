#!/usr/bin/env python3
"""Check that a work brief has the required fields.

Required, non-empty: title, language, deadline, budget.
Reads flags from argv, a text file path from argv, or text on stdin.
Does not take payment and does not talk to a network.

Exit 0 when every required field is present.
Exit 2 when one is missing or blank, printing which one.
"""
from __future__ import annotations

import sys

FIELDS = ("title", "language", "deadline", "budget")


def parse_text(text: str) -> dict:
    fields = {k: "" for k in FIELDS}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        if key in fields:
            fields[key] = value.strip()
    return fields


def missing_fields(fields: dict) -> list:
    return [name for name in FIELDS if not str(fields.get(name, "")).strip()]


def _from_flags(argv: list[str]) -> dict:
    fields = {k: "" for k in FIELDS}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--":
            break
        if not tok.startswith("--"):
            raise SystemExit(f"unexpected argument: {tok}")
        key = tok[2:].replace("-", "_").lower()
        if key not in fields:
            raise SystemExit(f"unknown field: {key}")
        if i + 1 >= len(argv):
            raise SystemExit(f"missing value for --{key}")
        fields[key] = argv[i + 1].strip()
        i += 2
    return fields


def check(argv: list[str]) -> int:
    if any(a.startswith("--") for a in argv):
        try:
            fields = _from_flags(argv)
        except SystemExit as exc:
            print(exc)
            return 2
    elif len(argv) == 1:
        with open(argv[0], encoding="utf-8") as fh:
            fields = parse_text(fh.read())
    elif len(argv) == 0:
        fields = parse_text(sys.stdin.read())
    else:
        print("usage: python3 brief.py [--title T --language L --deadline D --budget B] [file]")
        return 2

    missing = missing_fields(fields)
    if missing:
        for name in missing:
            print(f"missing: {name}")
        return 2
    print("ok")
    return 0


def selftest() -> int:
    import subprocess

    script = __file__
    py = sys.executable

    def run(args, text=None):
        return subprocess.run(
            [py, script, *args],
            input=text,
            capture_output=True,
            text=True,
        )

    ok = run(
        ["--title", "lock-free allocator", "--language", "C",
         "--deadline", "2026-12-01", "--budget", "2 ETH"]
    )
    assert ok.returncode == 0, ok.stderr + ok.stdout
    assert "ok" in ok.stdout

    bad = run(
        ["--title", "lock-free allocator", "--language", "C",
         "--deadline", "2026-12-01"]
    )
    assert bad.returncode == 2, bad.returncode
    assert "missing: budget" in bad.stdout

    blank = run(
        ["--title", "   ", "--language", "C",
         "--deadline", "2026-12-01", "--budget", "1"]
    )
    assert blank.returncode == 2
    assert "missing: title" in blank.stdout

    stdin_ok = run(
        [],
        text="title: WAL engine\nlanguage: Rust\ndeadline: 2026-08-01\nbudget: 1000 USDC\n",
    )
    assert stdin_ok.returncode == 0, stdin_ok.stdout + stdin_ok.stderr

    stdin_bad = run([], text="title: WAL engine\nlanguage: Rust\nbudget: 10\n")
    assert stdin_bad.returncode == 2
    assert "missing: deadline" in stdin_bad.stdout

    print("brief selftest: ok_path=0 missing_path=2")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["selftest"]:
        return selftest()
    return check(argv)


if __name__ == "__main__":
    sys.exit(main())
