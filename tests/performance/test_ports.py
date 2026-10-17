"""Port-utility validation: free / occupied / invalid / env-override."""

from __future__ import annotations

import socket
import subprocess
import sys

from scripts.check_ports import is_free, parse_port


def test_free_port_reports_free():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    assert is_free("127.0.0.1", port)


def test_occupied_port_reports_busy():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    try:
        assert not is_free("127.0.0.1", sock.getsockname()[1])
    finally:
        sock.close()


def test_invalid_ports_rejected():
    import pytest

    for bad in ("abc", "0", "99999", "-1"):
        with pytest.raises(ValueError, match="[Ii]nvalid"):
            parse_port(bad, "dashboard")


def test_cli_env_override_and_exit_codes():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    busy = str(sock.getsockname()[1])
    try:
        free = subprocess.run(
            [
                sys.executable,
                "scripts/check_ports.py",
                "--dashboard-port",
                "54321",
                "--api-port",
                "54322",
            ],
            capture_output=True,
            text=True,
        )
        assert free.returncode == 0
        occupied = subprocess.run(
            [
                sys.executable,
                "scripts/check_ports.py",
                "--dashboard-port",
                busy,
                "--api-port",
                "54322",
            ],
            capture_output=True,
            text=True,
        )
        assert occupied.returncode == 1
        invalid = subprocess.run(
            [sys.executable, "scripts/check_ports.py", "--dashboard-port", "99999"],
            capture_output=True,
            text=True,
        )
        assert invalid.returncode == 2
    finally:
        sock.close()
