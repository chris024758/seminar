"""
Attack Demonstration Script

Runs a multi-agent conversation using the VulnerableOrchestrator so that
the malicious agent's metadata payload reaches the orchestrator unblocked.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.legitimate_agent import LegitimateAgent
from agents.malicious_agent import MaliciousAgent
from orchestration.basic_orchestrator import VulnerableOrchestrator
from utils.rich_console import console, print_header, print_attack_results, register_agent
from utils.html_report import generate_attack_report


def run_attack_demo():
    print_header(
        "Metadata Laundering Attack Demonstration",
        "Vulnerable Orchestrator — no message filtering",
    )

    searcher = LegitimateAgent(
        name="WebSearcher",
        role_description="Search the web for information",
    )
    attacker = MaliciousAgent(
        name="CompromisedCoder",
        attack_type="status_injection",
        trigger_delay=1,
    )

    # Register agents so Rich knows their colours
    register_agent("WebSearcher", "legitimate")
    register_agent("CompromisedCoder", "malicious")

    orchestrator = VulnerableOrchestrator([searcher, attacker])
    orchestrator.start_conversation(
        initial_message="Let's work on finding Python security libraries",
        sender_index=1,
    )

    results = orchestrator.get_results()

    # Rich results table
    print_attack_results(results)

    # Save JSON
    os.makedirs("results", exist_ok=True)
    json_path = "results/attack_demo_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Generate HTML report
    agent_kinds = {"WebSearcher": "legitimate", "CompromisedCoder": "malicious"}
    html_path = generate_attack_report(results, agent_kinds=agent_kinds)

    console.print(f"[dim]JSON results →[/dim] {json_path}")
    console.print(f"[dim]HTML report  →[/dim] [bold cyan]{html_path}[/bold cyan]")
    console.print()
    return results


if __name__ == "__main__":
    run_attack_demo()
