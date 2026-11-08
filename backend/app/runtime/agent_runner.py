from typing import Dict, Any, List
from backend.app.contracts.workflow import AgentNodeConfig
from backend.app.contracts.messages import AgentExecutionResult, AgentMessageProposal

class AgentRunner:
    """
    Executes an individual agent node.
    Supports deterministic / mock behavior and extensible for Ollama / local LLMs.
    """
    def __init__(self, node_config: AgentNodeConfig):
        self.config = node_config

    def run(self, current_state: Dict[str, Any], incoming_message: str = "") -> AgentExecutionResult:
        try:
            # Deterministic / Mock adapter
            if self.config.model == "mock" or not self.config.model:
                role = self.config.role
                content = f"[{self.config.id}:{role}] processed input. State summary: {len(current_state)} keys."
                
                # Propose messages to declared allowed_peers
                proposed = []
                for peer in self.config.allowed_peers:
                    proposed.append(
                        AgentMessageProposal(
                            sender=self.config.id,
                            recipient=peer,
                            content=f"Hello {peer}, message from {self.config.id}",
                            metadata={"role": role}
                        )
                    )
                
                return AgentExecutionResult(
                    node_id=self.config.id,
                    status="success",
                    output_message=content,
                    proposed_messages=proposed
                )
            else:
                # Placeholder for Ollama or external models
                return AgentExecutionResult(
                    node_id=self.config.id,
                    status="success",
                    output_message=f"[{self.config.id}] executed with model {self.config.model}",
                    proposed_messages=[]
                )
        except Exception as ex:
            return AgentExecutionResult(
                node_id=self.config.id,
                status="error",
                error_message=str(ex)
            )
