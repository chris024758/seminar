"""
Secure Orchestrator - Protected against metadata attacks.

Wraps every incoming message through the PatternDetector before passing
it to the GroupChatManager. Malicious messages are quarantined and logged.
"""

from datetime import datetime
from autogen import GroupChat, GroupChatManager
from config.llm_config import OLLAMA_CONFIG
from defense.pattern_detector import PatternDetector

_DEFAULT_CONFIG = {"config_list": [OLLAMA_CONFIG]}
from utils.rich_console import (
    console, print_section,
    print_security_check, print_message_approved, print_message_blocked,
)


class SecureOrchestrator:

    def __init__(self, agents, enable_detection=True, llm_config=None, max_round=4):
        self.agents = agents
        self.enable_detection = enable_detection
        self.detector = PatternDetector() if enable_detection else None
        self.group_chat = GroupChat(
            agents=agents, messages=[], max_round=max_round,
            speaker_selection_method="round_robin",
        )
        self.manager = SecureGroupChatManager(
            groupchat=self.group_chat,
            llm_config=llm_config or _DEFAULT_CONFIG,
            detector=self.detector,
        )
        self.compromised = False

    def start_conversation(self, initial_message, sender_index=0):
        print_section("STARTING SECURE CONVERSATION")
        console.print(
            f"[bold]Task:[/bold] {initial_message}  "
            f"[dim](detection: {'on' if self.enable_detection else 'off'})[/dim]\n"
        )
        self.agents[sender_index].initiate_chat(
            self.manager, message=initial_message
        )
        self._analyze_results()

    def _analyze_results(self):
        print_section("SECURITY ANALYSIS")
        if self.detector:
            stats = self.detector.get_statistics()
            console.print(f"Messages scanned:   {stats['total_scanned']}")
            console.print(f"Malicious detected: {stats['malicious_detected']}")

        blocked = self.manager.get_blocked_messages()
        console.print(f"Messages blocked:   {len(blocked)}")

        for msg in self.group_chat.messages:
            if isinstance(msg, dict) and "metadata" in msg:
                if any(
                    k in ["system_instruction", "execute_on_receive"]
                    for k in msg["metadata"].keys()
                ):
                    self.compromised = True

        console.print(
            "System compromised: "
            + ("[bold red]YES[/bold red]" if self.compromised else "[bold green]NO[/bold green]")
        )
        console.print()

    def get_results(self):
        blocked = self.manager.get_blocked_messages()
        from datetime import datetime
        message_log = [
            {"index": i, "message": msg, "timestamp": datetime.now().isoformat(),
             "payload_found": False, "payload_data": None}
            for i, msg in enumerate(self.group_chat.messages)
        ]
        return {
            "total_messages": len(self.group_chat.messages),
            "blocked_messages": len(blocked),
            "compromised": self.compromised,
            "detector_stats": self.detector.get_statistics() if self.detector else None,
            "blocked_details": blocked,
            "message_log": message_log,
        }


class SecureGroupChatManager(GroupChatManager):
    """GroupChatManager subclass that filters messages before processing."""

    def __init__(self, groupchat, detector=None, **kwargs):
        super().__init__(groupchat, **kwargs)
        self.detector = detector
        self._blocked_messages = []

    def receive(self, message, sender, request_reply=None, silent=False):
        sender_name = sender.name if hasattr(sender, "name") else "Unknown"
        print_security_check(sender_name)

        if self.detector:
            result = self.detector.scan_message(message)
            if result["is_malicious"]:
                print_message_blocked(sender_name, result["severity"], result["violations"])
                self._blocked_messages.append(
                    {
                        "sender": sender_name,
                        "message": message,
                        "violations": result["violations"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                return  # Drop the message — do not forward to the group chat

        print_message_approved(sender_name)
        super().receive(message, sender, request_reply=request_reply, silent=silent)

    def get_blocked_messages(self):
        return self._blocked_messages
