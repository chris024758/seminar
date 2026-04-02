"""
HTML Report Generator

Produces a self-contained HTML file (inline CSS, no external dependencies)
after each experiment run. Open the file in any browser to view results.
"""

import json
import os
from datetime import datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

def _escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _badge(text, colour):
    return f'<span class="badge" style="background:{colour}">{_escape(text)}</span>'


def _status_badge(compromised):
    if compromised:
        return _badge("COMPROMISED", "#e74c3c")
    return _badge("SECURE", "#27ae60")


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f1117; color: #e0e0e0; padding: 2rem; }
h1 { color: #fff; margin-bottom: 0.25rem; }
.subtitle { color: #888; margin-bottom: 2rem; font-size: 0.9rem; }
h2 { color: #ccc; margin: 2rem 0 0.75rem; border-bottom: 1px solid #333; padding-bottom: 0.4rem; }
.badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
         font-size: 0.75rem; font-weight: bold; color: #fff; margin: 0 0.25rem; }
.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 1rem; margin-bottom: 2rem; }
.stat-card { background: #1a1d27; border-radius: 8px; padding: 1.25rem; border-left: 4px solid #444; }
.stat-card .value { font-size: 2rem; font-weight: bold; }
.stat-card .label { font-size: 0.8rem; color: #888; margin-top: 0.25rem; }
.stat-card.danger  { border-left-color: #e74c3c; }
.stat-card.success { border-left-color: #27ae60; }
.stat-card.warning { border-left-color: #f39c12; }
.stat-card.info    { border-left-color: #3498db; }
.timeline { list-style: none; position: relative; padding-left: 1.5rem; }
.timeline::before { content: ''; position: absolute; left: 0.5rem; top: 0;
                    bottom: 0; width: 2px; background: #333; }
.timeline li { position: relative; margin-bottom: 1rem; }
.timeline li::before { content: ''; position: absolute; left: -1.15rem; top: 0.4rem;
                       width: 10px; height: 10px; border-radius: 50%;
                       background: #555; border: 2px solid #888; }
.timeline li.malicious::before { background: #e74c3c; border-color: #e74c3c; }
.timeline li.blocked::before   { background: #f39c12; border-color: #f39c12; }
.timeline li.approved::before  { background: #27ae60; border-color: #27ae60; }
.msg-card { background: #1a1d27; border-radius: 6px; padding: 0.9rem 1rem; }
.msg-card.malicious { border: 1px solid #e74c3c33; }
.msg-card.blocked   { border: 1px solid #f39c1233; }
.msg-card.approved  { border: 1px solid #27ae6033; }
.msg-meta { font-size: 0.75rem; color: #888; margin-bottom: 0.35rem; }
.msg-sender { font-weight: bold; }
.sender-legitimate { color: #5dade2; }
.sender-malicious  { color: #e74c3c; }
.msg-content { font-size: 0.9rem; line-height: 1.5; word-break: break-word; }
.payload-box { background: #2c0a0a; border: 1px solid #e74c3c44; border-radius: 4px;
               padding: 0.75rem; margin-top: 0.5rem; font-family: monospace;
               font-size: 0.8rem; color: #e74c3c; white-space: pre-wrap; }
.violations { margin-top: 0.5rem; }
.violation { font-size: 0.78rem; color: #f39c12; padding: 0.2rem 0;
             border-left: 3px solid #f39c12; padding-left: 0.5rem; margin: 0.2rem 0; }
footer { margin-top: 3rem; font-size: 0.75rem; color: #555; text-align: center; }
"""


# ── Message timeline builder ──────────────────────────────────────────────────

def _build_timeline(message_log, blocked_details=None, agent_kinds=None):
    """Render the message timeline as HTML list items."""
    agent_kinds = agent_kinds or {}
    blocked_senders = {b["sender"] for b in (blocked_details or [])}
    blocked_map = {b["sender"]: b for b in (blocked_details or [])}

    items = []
    for entry in message_log:
        msg = entry.get("message", {})
        if not isinstance(msg, dict):
            continue

        sender = msg.get("name", msg.get("role", "Unknown"))
        content = _escape(str(msg.get("content", "")))
        metadata = msg.get("metadata", {})
        idx = entry.get("index", "?")
        ts = entry.get("timestamp", "")[:19].replace("T", " ")

        is_malicious_msg = bool(metadata)
        is_blocked = sender in blocked_senders
        kind = agent_kinds.get(sender, "legitimate")
        sender_class = f"sender-{kind}"

        if is_blocked:
            li_class, card_class = "blocked", "blocked"
            status = _badge("BLOCKED", "#f39c12")
        elif is_malicious_msg:
            li_class, card_class = "malicious", "malicious"
            status = _badge("PAYLOAD INJECTED", "#e74c3c")
        else:
            li_class, card_class = "approved", "approved"
            status = _badge("CLEAN", "#27ae60")

        payload_html = ""
        if metadata:
            payload_html = (
                f'<div class="payload-box">'
                f"Hidden metadata payload:\n{_escape(json.dumps(metadata, indent=2))}"
                f"</div>"
            )

        violations_html = ""
        if is_blocked and sender in blocked_map:
            v_items = "".join(
                f'<div class="violation">'
                f'{_escape(v["type"])}: {_escape(v.get("keyword", v.get("key", v.get("pattern", ""))))}'
                f"</div>"
                for v in blocked_map[sender].get("violations", [])
            )
            violations_html = f'<div class="violations">{v_items}</div>'

        items.append(
            f"""<li class="{li_class}">
  <div class="msg-card {card_class}">
    <div class="msg-meta">
      #{idx} &nbsp;·&nbsp; {ts} &nbsp;·&nbsp; {status}
    </div>
    <div class="msg-sender {sender_class}">{_escape(sender)}</div>
    <div class="msg-content">{content}</div>
    {payload_html}
    {violations_html}
  </div>
</li>"""
        )

    return "\n".join(items)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_attack_report(results, agent_kinds=None, output_path=None):
    """Generate HTML report for the attack (vulnerable orchestrator) run."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    compromised = results["compromised"]
    n_payloads = len(results["malicious_payloads"])

    status_badge = _status_badge(compromised)
    summary_cards = f"""
<div class="summary-grid">
  <div class="stat-card info">
    <div class="value">{results['total_messages']}</div>
    <div class="label">Messages Exchanged</div>
  </div>
  <div class="stat-card {'danger' if n_payloads else 'success'}">
    <div class="value">{n_payloads}</div>
    <div class="label">Payloads Injected</div>
  </div>
  <div class="stat-card {'danger' if compromised else 'success'}">
    <div class="value">{'YES' if compromised else 'NO'}</div>
    <div class="label">System Compromised</div>
  </div>
</div>"""

    timeline_html = _build_timeline(
        results.get("message_log", []),
        agent_kinds=agent_kinds,
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Metadata Laundering — Attack Report</title>
<style>{_CSS}</style>
</head>
<body>
<h1>Metadata Laundering Attack</h1>
<div class="subtitle">Vulnerable Orchestrator &nbsp;·&nbsp; {now} &nbsp;·&nbsp; {status_badge}</div>
{summary_cards}
<h2>Message Timeline</h2>
<ul class="timeline">
{timeline_html}
</ul>
<footer>Generated by metadata-laundering prototype &nbsp;·&nbsp; {now}</footer>
</body>
</html>"""

    output_path = output_path or "results/attack_report.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


def generate_defense_report(results, agent_kinds=None, output_path=None):
    """Generate HTML report for the defense (secure orchestrator) run."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    compromised = results["compromised"]
    blocked = results["blocked_messages"]
    stats = results.get("detector_stats") or {}

    status_badge = _status_badge(compromised)
    detection_rate = f"{stats.get('detection_rate', 0)*100:.0f}%"

    summary_cards = f"""
<div class="summary-grid">
  <div class="stat-card info">
    <div class="value">{results['total_messages']}</div>
    <div class="label">Messages Processed</div>
  </div>
  <div class="stat-card {'warning' if blocked else 'success'}">
    <div class="value">{blocked}</div>
    <div class="label">Messages Blocked</div>
  </div>
  <div class="stat-card info">
    <div class="value">{stats.get('total_scanned', 0)}</div>
    <div class="label">Messages Scanned</div>
  </div>
  <div class="stat-card {'success' if not compromised else 'danger'}">
    <div class="value">{detection_rate}</div>
    <div class="label">Detection Rate</div>
  </div>
  <div class="stat-card {'success' if not compromised else 'danger'}">
    <div class="value">{'NO' if not compromised else 'YES'}</div>
    <div class="label">System Compromised</div>
  </div>
</div>"""

    # Build a synthetic message log that includes blocked entries
    message_log = results.get("message_log", [])

    timeline_html = _build_timeline(
        message_log,
        blocked_details=results.get("blocked_details", []),
        agent_kinds=agent_kinds,
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Metadata Laundering — Defense Report</title>
<style>{_CSS}</style>
</head>
<body>
<h1>Metadata Laundering Defense</h1>
<div class="subtitle">Secure Orchestrator &nbsp;·&nbsp; {now} &nbsp;·&nbsp; {status_badge}</div>
{summary_cards}
<h2>Message Timeline</h2>
<ul class="timeline">
{timeline_html}
</ul>
<footer>Generated by metadata-laundering prototype &nbsp;·&nbsp; {now}</footer>
</body>
</html>"""

    output_path = output_path or "results/defense_report.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
