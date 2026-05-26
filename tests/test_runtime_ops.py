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
