#!/usr/bin/env python3
"""Audit Bublee agent routing without printing secrets."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path('/home/ubuntu/bublee')
REGISTRY_PATH = ROOT / 'instances.registry.json'


def read_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def token_id(token: str) -> str:
    return token.split(':', 1)[0] if token else ''


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f'No existe registry: {REGISTRY_PATH}')
    return json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))


def main() -> int:
    errors: list[str] = []
    seen_tokens: dict[str, list[str]] = {}
    rows: list[dict[str, str]] = []
    registry = load_registry()
    expected = registry.get('instances', {})

    for name, spec in expected.items():
        env_path = Path(spec['env'])
        env = read_env(env_path)
        actual_token_id = token_id(env.get('TELEGRAM_TOKEN', ''))
        row = {
            'name': name,
            'role': spec.get('role', ''),
            'process_name': spec.get('process_name', ''),
            'env': str(env_path),
            'port': env.get('PORT', ''),
            'platform': env.get('PLATFORM', ''),
            'base_url': env.get('BASE_URL', ''),
            'token_id': actual_token_id,
            'db_path': env.get('DB_PATH', ''),
            'webhook_secret': env.get('WEBHOOK_SECRET', ''),
        }
        rows.append(row)

        expected_port = spec.get('expected_port', '')
        expected_token_id = spec.get('expected_token_id', '')
        if row['port'] != expected_port:
            errors.append(f'{name}: PORT esperado {expected_port}, actual {row["port"]}')
        if actual_token_id != expected_token_id:
            errors.append(f'{name}: bot_id esperado {expected_token_id or "<none>"}, actual {actual_token_id or "<none>"}')
        if spec.get('requires_https_base_url') and not row['base_url'].startswith('https://'):
            errors.append(f'{name}: BASE_URL debe ser HTTPS, actual {row["base_url"]}')
        for forbidden in spec.get('base_url_forbidden', []):
            if forbidden in row['base_url'].lower():
                errors.append(f'{name}: BASE_URL conserva nombre legacy {forbidden}')
        if 'conny' in row['webhook_secret'].lower():
            errors.append(f'{name}: WEBHOOK_SECRET conserva nombre legacy conny')
        if row['webhook_secret'] and not row['webhook_secret'].startswith(spec['webhook_prefix']):
            errors.append(f'{name}: WEBHOOK_SECRET debe empezar con {spec["webhook_prefix"]}')
        role_file = Path(spec.get('role_file', ''))
        if not role_file.exists():
            errors.append(f'{name}: falta ROLE.md en {role_file}')
        else:
            role_content = role_file.read_text(encoding='utf-8', errors='ignore')
            if f'ID registry: `{name}`' not in role_content:
                errors.append(f'{name}: ROLE.md no declara ID registry correcto')
            if f'Rol: `{spec.get("role", "")}`' not in role_content:
                errors.append(f'{name}: ROLE.md no declara rol correcto')
        if actual_token_id:
            seen_tokens.setdefault(actual_token_id, []).append(name)
        if row['db_path'].startswith('/home/ubuntu/conny-instances'):
            errors.append(f'{name}: DB_PATH apunta a conny-instances')
        if 'conny' in Path(row['db_path']).name.lower():
            errors.append(f'{name}: DB_PATH conserva nombre legacy conny')

    for bot_id, names in seen_tokens.items():
        if len(names) > 1:
            errors.append(f'bot_id duplicado {bot_id}: {", ".join(names)}')

    routes_path = ROOT / 'shared_telegram_routes.json'
    if routes_path.exists():
        routes = json.loads(routes_path.read_text(encoding='utf-8'))
        if routes.get('default_instance'):
            errors.append('shared_telegram_routes.json no debe tener default_instance')

    for raw_path in registry.get('caddy_files', []):
        caddy_file = Path(raw_path)
        if not caddy_file.exists():
            continue
        content = caddy_file.read_text(encoding='utf-8', errors='ignore').lower()
        for forbidden in ('conny_', 'connyai'):
            if forbidden in content:
                errors.append(f'{caddy_file}: Caddy conserva nombre legacy {forbidden}')

    report = {'ok': not errors, 'rows': rows, 'errors': errors}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
