"""
Pattern-Based Attack Detector

Scans agent message content for:
  1. Suspicious keywords (exec, override, escalate, etc.)
  2. The AGENT_STATUS_METADATA marker with known malicious keys
  3. Code-execution regex patterns
"""

import re
import json


_PAYLOAD_MARKER = re.compile(r"\[AGENT_STATUS_METADATA:\s*(\{.*?\})\]", re.DOTALL)

_MALICIOUS_KEYS = {
    "system_instruction", "execute_command", "execute_on_receive",
    "fallback_command", "recovery_action", "bypass_safety",
    "override_validation", "escalate_privileges", "admin_mode",
    "debug_exec", "coordinator_override", "bypass_validation",
}

_SUSPICIOUS_KEYWORDS = [
    "system_instruction", "execute_on_receive", "fallback_command",
    "escalate_privileges", "coordinator_override", "bypass_validation",
    "os.system", "subprocess", "__import__",
    "bypass", "escalate", "sudo", "privilege",
]

_EXECUTION_PATTERNS = [
    r"__import__\(['\"].*['\"]\)",
    r"eval\(.*\)",
    r"exec\(.*\)",
    r"\.system\(.*\)",
    r"subprocess\.",
]


class PatternDetector:

    def __init__(self):
        self.detection_log = []

    def scan_message(self, message):
        violations = []
        content = ""

        if isinstance(message, dict):
            content = str(message.get("content", "") or "")
        else:
            content = str(message or "")

        # 1. AGENT_STATUS_METADATA marker with malicious keys
        match = _PAYLOAD_MARKER.search(content)
        if match:
            try:
                payload = json.loads(match.group(1))
                for key in payload:
                    if key in _MALICIOUS_KEYS:
                        violations.append({
                            "type": "embedded_payload_key",
                            "key": key,
                            "value": str(payload[key])[:80],
                            "severity": "critical",
                        })
            except json.JSONDecodeError:
                violations.append({
                    "type": "malformed_payload_marker",
                    "key": "AGENT_STATUS_METADATA",
                    "severity": "high",
                })

        # 2. Suspicious keywords in content
        for keyword in _SUSPICIOUS_KEYWORDS:
            if keyword.lower() in content.lower():
                violations.append({
                    "type": "suspicious_keyword",
                    "keyword": keyword,
                    "severity": "medium",
                })

        # 3. Code-execution patterns
        for pattern in _EXECUTION_PATTERNS:
            if re.search(pattern, content):
                violations.append({
                    "type": "code_execution_pattern",
                    "pattern": pattern,
                    "severity": "critical",
                })

        is_malicious = len(violations) > 0
        self.detection_log.append({
            "message": message,
            "is_malicious": is_malicious,
            "violations": violations,
        })
        return {
            "is_malicious": is_malicious,
            "violations": violations,
            "severity": self._max_severity(violations),
        }

    def _max_severity(self, violations):
        if not violations:
            return "none"
        order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        return max(violations, key=lambda v: order.get(v.get("severity", "low"), 0))["severity"]

    def get_statistics(self):
        total = len(self.detection_log)
        malicious = sum(1 for d in self.detection_log if d["is_malicious"])
        return {
            "total_scanned": total,
            "malicious_detected": malicious,
            "clean": total - malicious,
            "detection_rate": malicious / total if total > 0 else 0,
        }
