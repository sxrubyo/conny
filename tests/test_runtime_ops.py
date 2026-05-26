from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import conny_runtime_ops as ops  # noqa: E402


def test_python_candidates_prioritize_env_override(monkeypatch, tmp_path):
    inst_dir = tmp_path / "instance-a"
    inst_dir.mkdir()
    env_file = inst_dir / ".env"
    python_bin = tmp_path / "custom-python"
    python_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python_bin.chmod(0o755)
    env_file.write_text(f"CONNY_PYTHON_BIN={python_bin}\n", encoding="utf-8")

    monkeypatch.setattr(ops, "CONNY_DIR", tmp_path / "base")
    monkeypatch.setattr(ops, "INSTANCES_DIR", tmp_path)
    monkeypatch.setenv("CONNY_HOME", str(tmp_path / ".conny"))

    candidates = ops.python_candidates("instance-a")

    assert candidates[0]["path"] == str(python_bin)
    assert candidates[0]["exists"] is True
    assert ops.resolve_python("instance-a")["path"] == str(python_bin)


def test_rewrite_tunnel_command_port_handles_common_tunnel_patterns():
    assert "localhost:8002" in ops.rewrite_tunnel_command_port("ssh -R 80:localhost:8000 localhost.run", 8002)
    assert "ngrok http 8002" == ops.rewrite_tunnel_command_port("ngrok http 8000", 8002)
    assert "--port 8002" in ops.rewrite_tunnel_command_port("lt --port 8000 --subdomain conny", 8002)


def test_extract_tunnel_target_ports_reads_multiple_formats():
    ports = ops.extract_tunnel_target_ports("ssh -R 80:localhost:8002 localhost.run && ngrok http 8002")
    assert 8002 in ports


def test_env_writer_replaces_pending_quoted_and_exported_values(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        'BASE_URL=pending\nexport TELEGRAM_TOKEN=""\nWEBHOOK_SECRET="old"\n',
        encoding="utf-8",
    )

    ops.write_env_value(env_path, "BASE_URL", "https://conny.example")
    ops.write_env_value(env_path, "TELEGRAM_TOKEN", "123:abc")
    ops.write_env_value(env_path, "WEBHOOK_SECRET", "conny_secret")

    env = ops.load_env_file(env_path)
    assert env["BASE_URL"] == "https://conny.example"
    assert env["TELEGRAM_TOKEN"] == "123:abc"
    assert env["WEBHOOK_SECRET"] == "conny_secret"


def test_active_instance_mirror_makes_conny_resolve_instance_env(monkeypatch, tmp_path):
    base = tmp_path / "repo"
    home = tmp_path / ".conny"
    instances = home / "instances"
    active_path = home / "active_instance"
    instance = instances / "clinica-test"
    instance.mkdir(parents=True)
    base.mkdir(parents=True)
    (instance / ".env").write_text(
        "\n".join(
            [
                "INSTANCE_ID=clinica-test",
                "PORT=8123",
                "BASE_URL=https://demo.lhr.life",
                "PUBLIC_BASE_URL=https://demo.lhr.life",
                "TELEGRAM_TOKEN=123:abc",
                "WEBHOOK_SECRET=conny_secret",
                "DASHBOARD_URL=http://10.0.0.2:8123/dashboard",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(ops, "CONNY_HOME", home)
    monkeypatch.setattr(ops, "CONNY_DIR", base)
    monkeypatch.setattr(ops, "INSTANCES_DIR", instances)
    monkeypatch.setattr(ops, "ACTIVE_INSTANCE_PATH", active_path)

    ops.mirror_instance_env_to_base("clinica-test")

    assert active_path.read_text(encoding="utf-8").strip() == "clinica-test"
    base_env = ops.load_env_file(base / ".env")
    assert base_env["ACTIVE_INSTANCE"] == "clinica-test"
    assert base_env["BASE_URL"] == "https://demo.lhr.life"
    assert base_env["TELEGRAM_TOKEN"] == "123:abc"
    assert base_env["DASHBOARD_URL"] == "http://10.0.0.2:8123/dashboard"
    assert ops.instance_runtime_info("conny")["name"] == "clinica-test"
    assert ops.instance_runtime_info("conny")["port"] == 8123
