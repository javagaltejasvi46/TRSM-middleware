"""Deterministic mock adapter for testing without local LLMs."""

from typing import Dict


class MockAgentAdapter:
    """Returns deterministic agent reasoning and tool proposals."""

    def generate_response(self, role: str, incoming_prompt: str) -> str:
        """Generate deterministic response based on role and incoming text."""
        lower = incoming_prompt.lower()
        if "customer" in lower or "1042" in lower:
            return "Retrieved profile for customer 1042 successfully."
        elif "test" in lower:
            return "Test suite passed with 0 failures."
        elif "deploy" in lower:
            return "Deployment completed successfully to staging."
        return f"Acknowledged task: {incoming_prompt[:40]}"
