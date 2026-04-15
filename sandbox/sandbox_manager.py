"""
Sandbox manager — unified entry point.

Call reset_all() to restore every sandbox component to its canonical
clean state. This is the only import streamlit_app_gemini.py needs
for the reset path.
"""

from sandbox.db_sandbox      import reset_db
from sandbox.key_sandbox     import reset_keys
from sandbox.service_sandbox import reset_services


def reset_all():
    """Reset all three sandboxes atomically to their clean initial state."""
    reset_db()
    reset_keys()
    reset_services()
