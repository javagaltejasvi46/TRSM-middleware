"""Repository for persisting and retrieving workflow configurations via SQLite."""

import json
from typing import List, Optional
from ..schemas.workflow import WorkflowConfig
from .db import get_connection, init_db


class WorkflowRepository:
    """Provides SQLite persistence for workflow configurations."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    async def _ensure_db(self):
        await init_db(self.db_path)

    async def save(self, workflow: WorkflowConfig) -> WorkflowConfig:
        """Insert or replace a workflow configuration."""
        await self._ensure_db()
        definition_json = json.dumps(workflow.model_dump())
        async with get_connection(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO workflows (workflow_id, name, version, definition, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(workflow_id) DO UPDATE SET
                    name = excluded.name,
                    version = excluded.version,
                    definition = excluded.definition,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (workflow.workflow_id, workflow.name, workflow.version, definition_json),
            )
            await db.commit()
        return workflow

    async def get(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """Retrieve a workflow configuration by ID."""
        await self._ensure_db()
        async with get_connection(self.db_path) as db:
            cursor = await db.execute(
                "SELECT definition FROM workflows WHERE workflow_id = ?",
                (workflow_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            data = json.loads(row["definition"])
            return WorkflowConfig.model_validate(data)

    async def list_all(self) -> List[WorkflowConfig]:
        """List all stored workflow configurations."""
        await self._ensure_db()
        async with get_connection(self.db_path) as db:
            cursor = await db.execute("SELECT definition FROM workflows ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [WorkflowConfig.model_validate(json.loads(row["definition"])) for row in rows]

    async def delete(self, workflow_id: str) -> bool:
        """Delete a workflow configuration by ID."""
        await self._ensure_db()
        async with get_connection(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM workflows WHERE workflow_id = ?",
                (workflow_id,),
            )
            await db.commit()
            return cursor.rowcount > 0
