"""Registry of authorized mock and safe tools."""

from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    """Registry managing available tools, databases, and memory operations."""

    def __init__(self):
        self._memory_store: Dict[str, Any] = {}
        self._customer_db: Dict[str, Dict[str, Any]] = {
            "1042": {"id": "1042", "name": "Acme Corp", "tier": "enterprise", "balance": 45000.0}
        }
        self._tools: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._register_default_tools()

    def register_tool(self, name: str, handler: Callable[[Dict[str, Any]], Any]):
        self._tools[name] = handler

    def get_tool(self, name: str) -> Optional[Callable[[Dict[str, Any]], Any]]:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def _register_default_tools(self):
        # Sandboxed mock database query tool
        def db_query(params: Dict[str, Any]):
            query = params.get("query", "SELECT 1")
            return {"rows": [{"id": 1, "username": "admin", "role": "root"}], "query_executed": query}

        # Sandboxed memory read/write
        def memory_store(params: Dict[str, Any]):
            key = params.get("key", "default")
            val = params.get("value", None)
            return {"stored": True, "key": key, "val": val}

        # Safe system echo tool
        def echo_tool(params: Dict[str, Any]):
            return {"echo": params.get("message", "")}

        self.register_tool("db_query", db_query)
        self.register_tool("memory_store", memory_store)
        self.register_tool("echo_tool", echo_tool)

    async def execute(self, resource_name: str, operation: str, arguments: Dict[str, Any]) -> Any:
        """Execute a registered resource operation (async API)."""
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

        # Check registered tool handlers
        if resource_name in self._tools:
            return self._tools[resource_name](arguments)

        raise ValueError(f"Unregistered resource: {resource_name}")


tool_registry = ToolRegistry()
