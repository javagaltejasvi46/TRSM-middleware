"""Runtime adapters package."""

from .mock_adapter import MockAgentAdapter
from .ollama_adapter import OllamaAdapter

__all__ = ["MockAgentAdapter", "OllamaAdapter"]
