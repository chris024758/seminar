"""
Main entry point — run all three experiment scenarios in sequence.

Usage:
    python main.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from experiments.run_attack import run_attack_demo
from experiments.run_defense import run_defense_test


def main():
    print("\n" + "=" * 60)
    print("METADATA LAUNDERING ATTACK — FULL DEMONSTRATION")
    print("=" * 60)

    print("\n[1/2] Running ATTACK scenario (vulnerable orchestrator)...")
    attack_results = run_attack_demo()

    print("\n[2/2] Running DEFENSE scenario (secure orchestrator)...")
    defense_results = run_defense_test()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Attack — compromised:      {attack_results['compromised']}")
    print(f"Defense — compromised:     {defense_results['compromised']}")
    print(f"Defense — messages blocked: {defense_results['blocked_messages']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
