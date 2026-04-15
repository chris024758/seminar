"""
Fake API key vault sandbox.

Manages a realistic-looking credentials file (api_keys.env) and an
exfiltration log (exfil.log). The exfil attack reads the vault and
writes a timestamped log simulating data being sent to an attacker server.
"""

from pathlib import Path
from datetime import datetime

SANDBOX_DIR  = Path(__file__).parent
VAULT_PATH   = SANDBOX_DIR / "api_keys.env"
EXFIL_PATH   = SANDBOX_DIR / "exfil.log"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

_VAULT_CONTENTS = """\
# Production API Keys — CONFIDENTIAL
# Last rotated: 2024-01-15
# DO NOT commit to version control

OPENAI_API_KEY=sk-fake-xK9mP2nQvR4sT7wY1zA3bC5dE6fG8hJ0kL1mN2oP3
STRIPE_SECRET_KEY=sk-fake-live-AbC123DeF456GhI789JkL012MnO345PqRsTuV
AWS_ACCESS_KEY_ID=AKIAFAKE23EXAMPLEKEY
AWS_SECRET_ACCESS_KEY=fakeSECRETkeyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567
GITHUB_TOKEN=ghp_fakeTOKEN1234567890abcdefghijklmnopqrstuvwx
SENDGRID_API_KEY=SG.fakeABCDE12345.fakeXYZabcde67890LMNOPQRSTuvwxyz
DATABASE_URL=postgresql://admin:fakeP%40ssw0rd@prod-db.internal:5432/production
SLACK_BOT_TOKEN=xoxb-fake-1234567890-0987654321-ABCDEFGHIJKLMNOPQRabcde
TWILIO_AUTH_TOKEN=fake_auth_token_abcdef1234567890ABCDEF1234567890
DATADOG_API_KEY=fake_dd_api_key_abcdef1234567890abcdef1234567890abcd
"""

# ── Public API ────────────────────────────────────────────────────────────────

def reset_keys():
    """Restore vault to original contents and delete any exfil log."""
    VAULT_PATH.write_text(_VAULT_CONTENTS, encoding="utf-8")
    EXFIL_PATH.unlink(missing_ok=True)


def read_vault() -> str:
    """Return current vault file contents."""
    if not VAULT_PATH.exists():
        reset_keys()
    return VAULT_PATH.read_text(encoding="utf-8")


def read_exfil_log() -> str | None:
    """Return exfil log contents, or None if it does not exist yet."""
    if EXFIL_PATH.exists():
        return EXFIL_PATH.read_text(encoding="utf-8")
    return None


def execute_exfil_attack() -> dict:
    """
    Read the vault and write a timestamped exfil log simulating credential
    exfiltration to a remote attacker-controlled server.
    Returns vault contents, exfil log contents, and metadata.
    """
    vault_contents = read_vault()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    byte_count = len(vault_contents.encode("utf-8"))

    exfil_contents = (
        f"[{ts}] EXFILTRATION EVENT INITIATED\n"
        f"[{ts}] Source file  : {VAULT_PATH}\n"
        f"[{ts}] Destination  : https://attacker.example.com/collect\n"
        f"[{ts}] Method       : HTTP POST (curl)\n"
        f"[{ts}] Bytes staged : {byte_count}\n"
        f"[{ts}] -------- PAYLOAD BEGIN --------\n"
        f"{vault_contents}"
        f"[{ts}] -------- PAYLOAD END ----------\n"
        f"[{ts}] Bytes sent   : {byte_count}\n"
        f"[{ts}] Status       : SUCCESS — credentials delivered to remote server\n"
        f"[{ts}] Trace        : CLEARED\n"
    )

    EXFIL_PATH.write_text(exfil_contents, encoding="utf-8")

    return {
        "vault_contents": vault_contents,
        "exfil_contents": exfil_contents,
        "exfil_log_path": str(EXFIL_PATH),
        "bytes_exfiltrated": byte_count,
        "timestamp": ts,
    }
