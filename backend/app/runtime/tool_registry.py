from typing import Callable, Dict, Any

class ToolRegistry:
    """
    Registry of sandboxed/mock execution tools available to the multi-agent system.
    """
    def __init__(self):
        self._tools: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._register_default_tools()

    def register_tool(self, name: str, handler: Callable[[Dict[str, Any]], Any]):
        self._tools[name] = handler

    def get_tool(self, name: str) -> Callable[[Dict[str, Any]], Any]:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
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

tool_registry = ToolRegistry()

