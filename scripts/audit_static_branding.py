#!/usr/bin/env python3
"""Audit public static assets for legacy Conny branding."""
from __future__ import annotations

import json
from pathlib import Path

STATIC_ROOT = Path('/home/ubuntu/bublee/src/interfaces/web/static')
FORBIDDEN_PATTERNS = (
    'conny_logo',
    'conny_master_key',
    'conny_dev_mode',
)


def should_scan(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.ico', '.woff2'}:
        return False
    return True


def main() -> int:
    errors: list[str] = []

    for path in STATIC_ROOT.rglob('*'):
        rel = path.relative_to(STATIC_ROOT)
        lower_name = str(rel).lower()
        if 'conny_logo' in lower_name:
            errors.append(f'legacy static asset name: {rel}')
        if not should_scan(path):
            continue
        text = path.read_text(encoding='utf-8', errors='ignore').lower()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in text:
                errors.append(f'{rel}: contiene {pattern}')

    report = {'ok': not errors, 'root': str(STATIC_ROOT), 'errors': errors}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
