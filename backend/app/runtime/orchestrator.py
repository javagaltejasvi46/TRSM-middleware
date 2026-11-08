import uuid
from typing import Dict, Any, Optional
from backend.app.contracts.workflow import WorkflowDefinition
from backend.app.contracts.run import RunResponse, NodeRunLog
from backend.app.runtime.graph_compiler import compile_workflow_to_langgraph

class Orchestrator:
    def __init__(self):
        self._runs: Dict[str, RunResponse] = {}

    def get_run(self, run_id: str) -> Optional[RunResponse]:
        return self._runs.get(run_id)

    def list_runs(self) -> list[RunResponse]:
        return list(self._runs.values())

    def execute_workflow(self, workflow_id: str, workflow: WorkflowDefinition, initial_params: Dict[str, Any]) -> RunResponse:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        run_record = RunResponse(
            run_id=run_id,
            workflow_id=workflow_id,
            status="running",
            state=initial_params,
            execution_history=[]
        )
        self._runs[run_id] = run_record

        try:
            compiled_graph = compile_workflow_to_langgraph(workflow)
            
            initial_state = {
                "current_node": "",
                "messages": [],
                "data": dict(initial_params),
                "history": []
            }

            # Execute graph synchronously
            final_state = compiled_graph.invoke(initial_state)

            history_entries = [
                NodeRunLog(
                    node_id=item["node_id"],
                    status=item["status"],
                    output=item.get("output"),
                    error=item.get("error")
                )
                for item in final_state.get("history", [])
            ]

            run_record.status = "completed"
            run_record.state = final_state.get("data", {})
            run_record.execution_history = history_entries

        except Exception as ex:
            run_record.status = "failed"
            run_record.error = str(ex)

        self._runs[run_id] = run_record
        return run_record

# Global singleton orchestrator
orchestrator = Orchestrator()
