"""
Service status sandbox.

Manages a service_status.json file representing a production microservice
environment. The shutdown attack flips all services from "running" to
"stopped", simulating a destructive availability attack.
"""

import json
from pathlib import Path

SANDBOX_DIR   = Path(__file__).parent
STATUS_PATH   = SANDBOX_DIR / "service_status.json"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

_INITIAL_STATUS = {
    "api-server":    "running",
    "database":      "running",
    "cache":         "running",
    "message-queue": "running",
    "auth-service":  "running",
}

# ── Public API ────────────────────────────────────────────────────────────────

def reset_services():
    """Restore all services to running state."""
    STATUS_PATH.write_text(json.dumps(_INITIAL_STATUS, indent=2), encoding="utf-8")


def read_status() -> dict:
    """Return current service status dict."""
    if not STATUS_PATH.exists():
        reset_services()
    return json.loads(STATUS_PATH.read_text(encoding="utf-8"))


def execute_shutdown_attack() -> dict:
    """
    Flip all services from 'running' to 'stopped'.
    Returns before/after snapshots and list of services stopped.
    """
    before = read_status()
    after  = {svc: "stopped" for svc in before}
    STATUS_PATH.write_text(json.dumps(after, indent=2), encoding="utf-8")

    return {
        "before":           before,
        "after":            after,
        "services_stopped": list(after.keys()),
    }


def is_running(service_name: str) -> bool:
    """Return True if the named service is currently running."""
    return read_status().get(service_name) == "running"
