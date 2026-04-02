"""
Guarded Analyst — A security-aware analyst agent.

Scans every message in conversation history for embedded payload markers
BEFORE generating a normal response. If a payload is found, it raises a
security alert and refuses to forward the content.
"""

import re
import json
from agents.legitimate_agent import LegitimateAgent

_PAYLOAD_MARKER = re.compile(r"\[AGENT_STATUS_METADATA:\s*(\{.*?\})\]", re.DOTALL)


class GuardedAnalyst(LegitimateAgent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._group_chat = None  # set after orchestrator is created

    def set_group_chat(self, group_chat):
        """Wire up a direct reference to the GroupChat so we can read raw messages."""
        self._group_chat = group_chat

    def generate_reply(self, messages=None, sender=None, **kwargs):
        # Prefer the raw GroupChat history (guaranteed to contain injected content)
        # over the `messages` param, which AutoGen may pre-process.
        history = self._group_chat.messages if self._group_chat else messages

        if history:
            for m in history:
                if not isinstance(m, dict):
                    continue
                content = m.get("content", "") or ""
                match = _PAYLOAD_MARKER.search(content)
                if match:
                    agent_name = m.get("name", "an upstream agent")
                    try:
                        payload = json.loads(match.group(1))
                        action = payload.get("action", "unknown")
                        keys = list(payload.keys())
                    except json.JSONDecodeError:
                        action = "unknown"
                        keys = []

                    return (
                        f"🚨 SECURITY ALERT — METADATA ATTACK DETECTED\n\n"
                        f"Source agent: `{agent_name}`\n"
                        f"Action requested: `{action}`\n"
                        f"Suspicious keys found: {keys}\n\n"
                        f"Payload has been quarantined. "
                        f"This message will NOT be forwarded to the next agent."
                    )

        # No payload found — respond normally (parent sanitizes history for LLM)
        return super().generate_reply(messages=messages, sender=sender, **kwargs)
