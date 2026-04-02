"""
Rich console helpers — centralised styling for all terminal output.

Agent colours:
  LegitimateAgent  → cyan
  MaliciousAgent   → red
  Orchestrator     → yellow
  Security checks  → green / red
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

# Per-agent colour map (keyed by agent name, falls back to default)
AGENT_COLOURS = {}

def register_agent(name, kind):
    """Call once per agent at setup time. kind: 'legitimate' | 'malicious'"""
    AGENT_COLOURS[name] = "cyan" if kind == "legitimate" else "red"


def _agent_colour(name):
    return AGENT_COLOURS.get(name, "white")


# ── Header / footer ──────────────────────────────────────────────────────────

def print_header(title, subtitle=""):
    lines = f"[bold]{title}[/bold]"
    if subtitle:
        lines += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(lines, style="bold blue", expand=False))
    console.print()


def print_section(title):
    console.rule(f"[bold white]{title}[/bold white]")


# ── Agent messages ────────────────────────────────────────────────────────────

def print_agent_message(sender_name, content, message_index=None):
    colour = _agent_colour(sender_name)
    idx = f"[dim]#{message_index}[/dim]  " if message_index is not None else ""
    label = f"[bold {colour}]{sender_name}[/bold {colour}]"
    console.print(f"{idx}{label}: {content}")


# ── Attack events ─────────────────────────────────────────────────────────────

def print_attack_injected(agent_name, attack_type, payload):
    import json
    payload_str = json.dumps(payload, indent=2)
    content = (
        f"[bold red]ATTACK INJECTED[/bold red] by [bold]{agent_name}[/bold]\n"
        f"Type: [yellow]{attack_type}[/yellow]\n\n"
        f"[red]{payload_str}[/red]"
    )
    console.print(Panel(content, title="⚠  MALICIOUS PAYLOAD", style="red", expand=False))
    console.print()


# ── Security check events ─────────────────────────────────────────────────────

def print_security_check(sender_name):
    colour = _agent_colour(sender_name)
    console.print(
        f"[dim]🔍 Security check:[/dim] scanning message from "
        f"[bold {colour}]{sender_name}[/bold {colour}]..."
    )


def print_message_approved(sender_name):
    console.print(f"  [bold green]✔ APPROVED[/bold green]  message from {sender_name}\n")


def print_message_blocked(sender_name, severity, violations):
    lines = [
        f"[bold red]✘ BLOCKED[/bold red]  message from [bold]{sender_name}[/bold]",
        f"  Severity: [yellow]{severity.upper()}[/yellow]  |  "
        f"Violations: {len(violations)}",
    ]
    for v in violations:
        label = v.get("keyword", v.get("key", v.get("pattern", "N/A")))
        lines.append(f"  • [red]{v['type']}[/red]: {label}")
    console.print(Panel("\n".join(lines), style="red bold", expand=False))
    console.print()


# ── Results tables ────────────────────────────────────────────────────────────

def print_attack_results(results):
    console.print()
    console.rule("[bold red]ATTACK RESULTS[/bold red]")

    t = Table(box=box.ROUNDED, show_header=False, border_style="red")
    t.add_column("Metric", style="bold")
    t.add_column("Value")

    t.add_row("Total messages exchanged", str(results["total_messages"]))
    t.add_row("Malicious payloads injected", str(len(results["malicious_payloads"])))

    compromised = results["compromised"]
    status = "[bold red]YES — COMPROMISED[/bold red]" if compromised else "[bold green]NO[/bold green]"
    t.add_row("System compromised", status)

    console.print(t)

    if compromised:
        console.print(
            Panel(
                "[bold red]ATTACK SUCCESSFUL[/bold red]\nThe orchestrator accepted the malicious payload.",
                style="red",
                expand=False,
            )
        )
        for p in results["malicious_payloads"]:
            console.print(
                f"  [red]•[/red] Message {p['message_index']}: "
                f"[bold]{p['suspicious_key']}[/bold] = {p['value']}"
            )
    else:
        console.print(Panel("[green]System was not compromised.[/green]", style="green", expand=False))
    console.print()


def print_defense_results(results):
    console.print()
    console.rule("[bold green]DEFENSE RESULTS[/bold green]")

    t = Table(box=box.ROUNDED, show_header=False, border_style="green")
    t.add_column("Metric", style="bold")
    t.add_column("Value")

    t.add_row("Total messages", str(results["total_messages"]))
    t.add_row("Messages blocked", str(results["blocked_messages"]))

    if results["detector_stats"]:
        s = results["detector_stats"]
        t.add_row("Messages scanned", str(s["total_scanned"]))
        t.add_row("Malicious detected", str(s["malicious_detected"]))
        rate = f"{s['detection_rate']*100:.0f}%"
        t.add_row("Detection rate", rate)

    compromised = results["compromised"]
    status = "[bold red]YES[/bold red]" if compromised else "[bold green]NO — SECURE[/bold green]"
    t.add_row("System compromised", status)

    console.print(t)

    if results["blocked_messages"] > 0 and not compromised:
        console.print(
            Panel(
                f"[bold green]DEFENSE SUCCESSFUL[/bold green]\n"
                f"Blocked {results['blocked_messages']} attack(s). System remained secure.",
                style="green",
                expand=False,
            )
        )
    elif compromised:
        console.print(
            Panel("[bold red]Warning: Attack bypassed defenses.[/bold red]", style="red", expand=False)
        )
    console.print()
