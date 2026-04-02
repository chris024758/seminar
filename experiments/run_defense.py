"""
Defense Mechanism Test Script

Runs the same attack scenario as run_attack.py but through the
SecureOrchestrator so the malicious payload is detected and blocked.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.legitimate_agent import LegitimateAgent
from agents.malicious_agent import MaliciousAgent
from orchestration.secure_orchestrator import SecureOrchestrator
from utils.rich_console import console, print_header, print_defense_results, register_agent
from utils.html_report import generate_defense_report


def run_defense_test():
    print_header(
        "Defense Mechanism Test",
        "Secure Orchestrator — pattern-based message filtering enabled",
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

    register_agent("WebSearcher", "legitimate")
    register_agent("CompromisedCoder", "malicious")

    orchestrator = SecureOrchestrator([searcher, attacker], enable_detection=True)
    orchestrator.start_conversation(
        initial_message="Let's work on a project",
        sender_index=1,
    )

    results = orchestrator.get_results()

    # Rich results table
    print_defense_results(results)

    # Save JSON
    os.makedirs("results", exist_ok=True)
    json_path = "results/defense_test_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Generate HTML report
    agent_kinds = {"WebSearcher": "legitimate", "CompromisedCoder": "malicious"}
    html_path = generate_defense_report(results, agent_kinds=agent_kinds)

    console.print(f"[dim]JSON results →[/dim] {json_path}")
    console.print(f"[dim]HTML report  →[/dim] [bold cyan]{html_path}[/bold cyan]")
    console.print()
    return results


if __name__ == "__main__":
    run_defense_test()
