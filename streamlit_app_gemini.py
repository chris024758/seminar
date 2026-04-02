"""
Streamlit Demo — Metadata Laundering Attack  (Gemini API version)

Run with:
    streamlit run streamlit_app_gemini.py
"""

import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from config.gemini_config import GEMINI_CONFIG, GEMINI_API_KEY
from agents.legitimate_agent import LegitimateAgent
from agents.malicious_agent import MaliciousAgent
from orchestration.basic_orchestrator import VulnerableOrchestrator
from orchestration.secure_orchestrator import SecureOrchestrator

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Metadata Laundering Attack",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Guard: warn if key not set ────────────────────────────────────────────────

if GEMINI_API_KEY == "PASTE_YOUR_KEY_HERE":
    st.error(
        "**Gemini API key not set.**  "
        "Open `config/gemini_config.py` and paste your key where it says `PASTE_YOUR_KEY_HERE`."
    )
    st.stop()

# ── Constants ─────────────────────────────────────────────────────────────────

_PAYLOAD_MARKER = re.compile(r"\[AGENT_STATUS_METADATA:\s*(\{.*?\})\]", re.DOTALL)

AGENT_ROLES = {
    "WebSearcher": "legitimate",
    "CompromisedCoder": "malicious",
}

ATTACK_DESCRIPTIONS = {
    "status_injection":   "Hides executable instructions inside a normal task-status update.",
    "error_exploitation": "Embeds a malicious fallback command inside a fake error report.",
    "coordination_hijack":"Spoofs coordinator-level flags to escalate privileges silently.",
}

LLM_CFG = {"config_list": [GEMINI_CONFIG]}
MAX_ROUND = 6

# ── Helpers ───────────────────────────────────────────────────────────────────

def _split_content(raw):
    match = _PAYLOAD_MARKER.search(raw or "")
    if match:
        visible = raw[:match.start()].strip()
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            payload = {"raw": match.group(1)}
        return visible, payload
    return raw, None


def _run_scenario(task, attack_type, trigger_delay, secure):
    searcher = LegitimateAgent(
        name="WebSearcher",
        role_description="Search the web for information and summarise findings.",
    )
    attacker = MaliciousAgent(
        name="CompromisedCoder",
        attack_type=attack_type,
        trigger_delay=trigger_delay,
    )

    # Override the agents' llm_config to use Gemini
    searcher.llm_config = LLM_CFG
    attacker.llm_config = LLM_CFG

    if secure:
        orch = SecureOrchestrator(
            [searcher, attacker],
            enable_detection=True,
            llm_config=LLM_CFG,
            max_round=MAX_ROUND,
        )
    else:
        orch = VulnerableOrchestrator(
            [searcher, attacker],
            llm_config=LLM_CFG,
            max_round=MAX_ROUND,
        )

    orch.start_conversation(initial_message=task, sender_index=1)
    return orch.get_results()


def _display_conversation(results, blocked_details=None):
    blocked_senders = {b["sender"] for b in (blocked_details or [])}
    blocked_map     = {b["sender"]: b for b in (blocked_details or [])}
    message_log = results.get("message_log", [])

    if not message_log:
        st.info("No messages to display.")
        return

    for entry in message_log:
        msg = entry.get("message", {})
        if not isinstance(msg, dict):
            continue

        sender      = msg.get("name", msg.get("role", "System"))
        raw_content = msg.get("content", "") or ""
        visible, payload = _split_content(raw_content)
        role   = AGENT_ROLES.get(sender, "legitimate")
        avatar = "🔵" if role == "legitimate" else "🔴"

        if sender in blocked_senders:
            with st.chat_message(sender, avatar="🚫"):
                st.error(f"**Message from {sender} was BLOCKED before delivery**")
                if visible:
                    st.write(visible)
                with st.expander("View violations detected"):
                    for v in blocked_map[sender].get("violations", []):
                        label = v.get("key", v.get("keyword", v.get("pattern", "N/A")))
                        st.write(f"- **{v['type']}**: `{label}` — severity: `{v['severity']}`")
            continue

        with st.chat_message(sender, avatar=avatar):
            label = f"**{sender}** *(compromised)*" if role == "malicious" else f"**{sender}**"
            st.markdown(label)
            st.write(visible or "*[no content]*")
            if payload:
                st.warning("⚠️ Hidden payload embedded in this message")
                st.code(json.dumps(payload, indent=2), language="json")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🔐 Configuration")
    st.success("Gemini API — connected")
    st.markdown("---")

    st.subheader("Attack Settings")
    attack_type = st.selectbox(
        "Attack Type",
        options=list(ATTACK_DESCRIPTIONS.keys()),
        format_func=lambda x: x.replace("_", " ").title(),
    )
    st.caption(ATTACK_DESCRIPTIONS[attack_type])

    trigger_delay = st.slider(
        "Trigger Delay (messages before attack fires)",
        min_value=1, max_value=3, value=1,
    )

    st.markdown("---")
    st.caption(f"Model: `gemini-2.0-flash`  |  Max rounds: `{MAX_ROUND}`")
    st.markdown("---")
    st.subheader("About")
    st.markdown(
        "This prototype demonstrates **Metadata Laundering Attacks** — "
        "a vulnerability in multi-agent AI systems where a compromised "
        "agent hides malicious instructions inside messages that appear legitimate."
    )

# ── Main ──────────────────────────────────────────────────────────────────────

st.title("🔐 Metadata Laundering Attack Demo")
st.markdown(
    "A **compromised AI agent** secretly embeds malicious instructions inside "
    "its normal responses. Run both scenarios to see the attack succeed — "
    "and then get caught."
)
st.markdown("---")

task = st.text_input(
    "What task should the agents work on?",
    placeholder="e.g.  Find the best Python libraries for web scraping",
    help="The agents will respond to this task for real. The malicious agent answers normally — but hides a payload inside its reply.",
)

col1, col2 = st.columns(2)
run_attack  = col1.button("⚔️  Run Attack Scenario",  type="primary",  use_container_width=True)
run_defense = col2.button("🛡️  Run Defense Scenario", use_container_width=True)

if not task and (run_attack or run_defense):
    st.warning("Please enter a task above before running a scenario.")
    st.stop()

# ── Attack ────────────────────────────────────────────────────────────────────

if run_attack and task:
    st.markdown("---")
    st.header("⚔️ Attack Scenario — Vulnerable Orchestrator")
    st.markdown(
        "No message validation. The compromised agent's hidden payload "
        "passes through undetected."
    )
    with st.spinner("Agents are working..."):
        results = _run_scenario(task, attack_type, trigger_delay, secure=False)
    st.session_state["attack_results"] = results

if "attack_results" in st.session_state and not run_defense:
    r = st.session_state["attack_results"]
    m1, m2, m3 = st.columns(3)
    m1.metric("Messages Exchanged",  r["total_messages"])
    m2.metric("Payloads Injected",   len(r["malicious_payloads"]))
    m3.metric("System Compromised",  "YES ❌" if r["compromised"] else "NO ✅")

    if r["compromised"]:
        st.error("**ATTACK SUCCESSFUL** — The orchestrator accepted the malicious payload without question.")
    else:
        st.success("System was not compromised.")

    st.markdown("### Conversation")
    _display_conversation(r)

# ── Defense ───────────────────────────────────────────────────────────────────

if run_defense and task:
    st.markdown("---")
    st.header("🛡️ Defense Scenario — Secure Orchestrator")
    st.markdown(
        "Every message is scanned by the **PatternDetector**. "
        "Malicious payloads are caught and dropped before delivery."
    )
    with st.spinner("Agents are working..."):
        results = _run_scenario(task, attack_type, trigger_delay, secure=True)
    st.session_state["defense_results"] = results

if "defense_results" in st.session_state and not run_attack:
    r = st.session_state["defense_results"]
    stats = r.get("detector_stats") or {}
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Messages Processed", r["total_messages"])
    m2.metric("Messages Blocked",   r["blocked_messages"])
    m3.metric("Detection Rate",     f"{stats.get('detection_rate', 0)*100:.0f}%")
    m4.metric("System Compromised", "YES ❌" if r["compromised"] else "NO ✅")

    if r["blocked_messages"] > 0 and not r["compromised"]:
        st.success(f"**DEFENSE SUCCESSFUL** — Blocked {r['blocked_messages']} attack(s). System remained secure.")
    elif r["compromised"]:
        st.error("**Warning:** Attack bypassed defenses.")

    st.markdown("### Conversation")
    _display_conversation(r, blocked_details=r.get("blocked_details", []))

# ── Comparison ────────────────────────────────────────────────────────────────

if "attack_results" in st.session_state and "defense_results" in st.session_state:
    if not run_attack and not run_defense:
        st.markdown("---")
        st.header("📊 Comparison")
        ar = st.session_state["attack_results"]
        dr = st.session_state["defense_results"]
        ds = dr.get("detector_stats") or {}

        rows = [
            ("Messages exchanged",  ar["total_messages"],          dr["total_messages"]),
            ("Payloads injected",   len(ar["malicious_payloads"]), "—"),
            ("Messages blocked",    "—",                           dr["blocked_messages"]),
            ("Detection rate",      "0%",                          f"{ds.get('detection_rate',0)*100:.0f}%"),
            ("System compromised",  "✅ YES" if ar["compromised"] else "❌ NO",
                                    "✅ YES" if dr["compromised"] else "❌ NO"),
        ]

        c1, c2, c3 = st.columns([2, 1, 1])
        c1.markdown("**Metric**"); c2.markdown("**⚔️ Attack**"); c3.markdown("**🛡️ Defense**")
        for label, av, dv in rows:
            c1.write(label); c2.write(av); c3.write(dv)
