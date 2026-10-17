"""Safe port-conflict checker for dashboard / API services.

Usage:
    python scripts/check_ports.py [--host 127.0.0.1] [--dashboard-port 8501] [--api-port 8000]

Reads N100_DASHBOARD_PORT / N100_API_PORT env overrides when flags are
omitted. Never kills processes; exit code 1 when a required port is busy.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys


def parse_port(value: str, name: str) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {name} port {value!r}: must be an integer 1-65535")
    if not 1 <= port <= 65535:
        raise ValueError(f"Invalid {name} port {port}: must be 1-65535")
    return port


def is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def check_service(name: str, host: str, port: int) -> bool:
    if is_free(host, port):
        print(f"[FREE] {name} {host}:{port} is available")
        return True
    print(
        f"[BUSY] {name} {host}:{port} is occupied. "
        f"Resolve with: set {name}_PORT=<free-port>  (never auto-killed)",
        file=sys.stderr,
    )
    print(
        f"       Hint (Windows): netstat -ano | findstr :{port}  "
        f"then inspect the PID in Task Manager.",
        file=sys.stderr,
    )
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check dashboard/API ports")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--dashboard-port", default=os.environ.get("N100_DASHBOARD_PORT", "8501")
    )
    parser.add_argument("--api-port", default=os.environ.get("N100_API_PORT", "8000"))
    parser.add_argument(
        "--api-required",
        action="store_true",
        help="fail if the API port is busy (default: informational only)",
    )
    args = parser.parse_args()
    try:
        dash_port = parse_port(args.dashboard_port, "dashboard")
        api_port = parse_port(args.api_port, "api")
    except ValueError as exc:
        print(f"Port error: {exc}", file=sys.stderr)
        return 2
    dash_ok = check_service("dashboard", args.host, dash_port)
    api_free = is_free(args.host, api_port)
    print(
        f"[{'FREE' if api_free else 'BUSY'}] api {args.host}:{api_port} "
        f"{'is available' if api_free else '(no API service in this repo; informational)'}"
    )
    if not dash_ok:
        return 1
    if args.api_required and not api_free:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
