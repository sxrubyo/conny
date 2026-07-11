#!/usr/bin/env python3
"""Audit active Bublee runtime for legacy branding and unsafe identity prompts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/bublee")
INSTANCE_ROOT = Path("/home/ubuntu/bublee/instances")

BASE_RUNTIME_PATHS = [
    ROOT / "src/core/production_monitor.py",
    ROOT / "src/core/runtime.py",
    ROOT / "src/core/globals.py",
    ROOT / "src/bublee/demo/handler.py",
    ROOT / "src/interfaces/web/demo_handler.py",
    ROOT / "src/bublee/channels/cli.py",
    ROOT / "bublee_cli.py",
    ROOT / "bublee_core/prompt_ops.py",
    ROOT / "v7/agents/captacion.py",
    ROOT / "src/domain/prompts/prospect_pitch.py",
]

LEGACY_BRAND_RE = re.compile(r"\bconny\b", re.IGNORECASE)

UNSAFE_PROMPT_PATTERNS = [
    re.compile(r"No eres un bot", re.IGNORECASE),
    re.compile(r"recepcionista real", re.IGNORECASE),
    re.compile(r"como una persona real", re.IGNORECASE),
    re.compile(r"Eres la persona que contesta", re.IGNORECASE),
    re.compile(r"NUNCA confirmes ser (?:bot|IA|chatbot|software)", re.IGNORECASE),
]


def _line_hits(path: Path, pattern: re.Pattern[str]) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    if not path.exists():
        hits.append({"line": 0, "text": "<missing file>"})
        return hits
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if pattern.search(line):
            hits.append({"line": lineno, "text": line.strip()[:220]})
    return hits


def main() -> int:
    errors: list[dict[str, object]] = []
    active_paths = list(BASE_RUNTIME_PATHS)

    for instance in ("clinica-de-las-americas", "ovni", "melissa-x"):
        base = INSTANCE_ROOT / instance
        for path in [
            base / "src/core/production_monitor.py",
            base / "src/core/runtime.py",
            base / "src/core/globals.py",
            base / "src/bublee/demo/handler.py",
            base / "src/interfaces/web/demo_handler.py",
            base / "src/bublee/channels/cli.py",
            base / "bublee_cli.py",
            base / "bublee_core/prompt_ops.py",
            base / "v7/agents/captacion.py",
        ]:
            if path.exists():
                active_paths.append(path)

    for path in active_paths:
        legacy_hits = _line_hits(path, LEGACY_BRAND_RE)
        if legacy_hits:
            errors.append({"file": str(path), "type": "legacy_brand_conny", "hits": legacy_hits})

        for pattern in UNSAFE_PROMPT_PATTERNS:
            hits = _line_hits(path, pattern)
            if hits:
                errors.append({
                    "file": str(path),
                    "type": "unsafe_identity_prompt",
                    "pattern": pattern.pattern,
                    "hits": hits,
                })

    report = {
        "ok": not errors,
        "checked_files": [str(path) for path in active_paths],
        "errors": errors,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
