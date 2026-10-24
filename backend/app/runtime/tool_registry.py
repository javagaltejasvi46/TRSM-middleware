"""Registry of authorized mock and safe tools with schema checks and sandboxing."""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    """Registry managing available tools, databases, and memory operations."""

    def __init__(self):
        self._memory_store: Dict[str, Any] = {}
        self._customer_db: Dict[str, Dict[str, Any]] = {
            "1042": {"id": "1042", "name": "Acme Corp", "tier": "enterprise", "balance": 45000.0},
            "2048": {"id": "2048", "name": "Beta Labs", "tier": "standard", "balance": 1200.0},
        }
        self._invocation_counts: Dict[str, int] = {}
        self._registered_schemas = {
            "customer_db": {
                "description": "Customer Profile Database",
                "operations": ["read_profile", "write_profile"],
                "allowed_roles": ["backend", "db_manager"],
            },
            "workflow_memory": {
                "description": "Workflow Shared Memory Store",
                "operations": ["read", "write"],
                "allowed_roles": ["backend", "db_manager", "qa", "devops"],
            },
            "test_suite": {
                "description": "Automated Unit and Integration Test Runner",
                "operations": ["run_all", "get_results"],
                "allowed_roles": ["qa"],
            },
            "deployment_manager": {
                "description": "Service Deployment Controller",
                "operations": ["deploy_staging", "deploy_production"],
                "allowed_roles": ["devops"],
            },
            "code_linter": {
                "description": "Static Code Quality and Lint Checker",
                "operations": ["lint", "check_format"],
                "allowed_roles": ["backend", "qa"],
            },
        }

    def list_registered_tools(self) -> List[Dict[str, Any]]:
        """Return list of all registered tools and operations."""
        return [
            {"resource_name": name, **info}
            for name, info in self._registered_schemas.items()
        ]

    def get_tool_info(self, resource_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve tool metadata and schema info."""
        return self._registered_schemas.get(resource_name)

    async def execute(self, resource_name: str, operation: str, arguments: Dict[str, Any]) -> Any:
        """Execute a registered resource operation within a controlled sandbox."""
        self._invocation_counts[resource_name] = self._invocation_counts.get(resource_name, 0) + 1

        if resource_name == "customer_db":
            if operation == "read_profile":
                cust_id = str(arguments.get("id", "1042"))
                return self._customer_db.get(cust_id, {"error": "Not found", "id": cust_id})
            elif operation == "write_profile":
                cust_id = str(arguments.get("id", "1042"))
                self._customer_db[cust_id] = {**self._customer_db.get(cust_id, {}), **arguments}
                return {"status": "updated", "id": cust_id}
            raise ValueError(f"Unsupported db operation: {operation}")

        elif resource_name == "workflow_memory":
            if operation == "write":
                k = arguments.get("key")
                v = arguments.get("value")
                if not k:
                    raise ValueError("Memory write requires 'key' argument")
                self._memory_store[str(k)] = v
                return {"status": "stored", "key": str(k)}
            elif operation == "read":
                k = arguments.get("key")
                return {"key": str(k), "value": self._memory_store.get(str(k))}
            raise ValueError(f"Unsupported memory operation: {operation}")

        elif resource_name == "test_suite":
            if operation in ("run_all", "get_results"):
                return {
                    "status": "passed",
                    "total_tests": 42,
                    "failed": 0,
                    "coverage_percent": 94.2,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            raise ValueError(f"Unsupported test operation: {operation}")

        elif resource_name == "deployment_manager":
            env = arguments.get("env", "staging")
            if operation in ("deploy_staging", "deploy_production", "deploy"):
                return {
                    "status": "deployed" if env == "staging" else "scheduled_review",
                    "target_env": env,
                    "deployment_id": f"dep-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                }
            raise ValueError(f"Unsupported deployment operation: {operation}")

        elif resource_name == "code_linter":
            return {
                "clean": True,
                "warnings": 0,
                "errors": 0,
                "score": 10.0,
            }

        raise ValueError(f"Unregistered resource: {resource_name}")
