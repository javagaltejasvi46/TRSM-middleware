"""Registry of authorized mock and safe tools."""

from typing import Any, Callable, Dict


class ToolRegistry:
    """Registry managing available tools, databases, and memory operations."""

    def __init__(self):
        self._memory_store: Dict[str, Any] = {}
        self._customer_db: Dict[str, Dict[str, Any]] = {
            "1042": {"id": "1042", "name": "Acme Corp", "tier": "enterprise", "balance": 45000.0}
        }

    async def execute(self, resource_name: str, operation: str, arguments: Dict[str, Any]) -> Any:
        """Execute a registered resource operation."""
        if resource_name == "customer_db":
            if operation == "read_profile":
                cust_id = arguments.get("id", "1042")
                return self._customer_db.get(cust_id, {"error": "Not found"})
            elif operation == "write_profile":
                cust_id = arguments.get("id")
                if cust_id:
                    self._customer_db[cust_id] = arguments
                    return {"status": "updated", "id": cust_id}
            raise ValueError(f"Unsupported db operation: {operation}")

        elif resource_name == "workflow_memory":
            if operation == "write":
                k = arguments.get("key")
                v = arguments.get("value")
                self._memory_store[k] = v
                return {"status": "stored", "key": k}
            elif operation == "read":
                k = arguments.get("key")
                return {"key": k, "value": self._memory_store.get(k)}
            raise ValueError(f"Unsupported memory operation: {operation}")

        elif resource_name == "test_suite":
            return {"status": "passed", "total_tests": 42, "failed": 0}

        elif resource_name == "deployment_manager":
            return {"status": "scheduled", "env": arguments.get("env", "staging")}

        raise ValueError(f"Unregistered resource: {resource_name}")
