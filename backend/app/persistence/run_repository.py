"""Repository for persisting and retrieving workflow execution runs via SQLite."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from .db import get_connection, init_db
from .models import RunRecord


class RunRepository:
    """Provides SQLite persistence for execution run states and summaries."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    async def _ensure_db(self):
        await init_db(self.db_path)

    async def create_run(
        self,
        run_id: str,
        workflow_id: str,
        status: str,
        enable_trsm: bool,
        task: str,
        summary: Optional[Dict[str, Any]] = None,
    ) -> RunRecord:
        """Record the initial state of a workflow execution run."""
        await self._ensure_db()
        summary_json = json.dumps(summary) if summary else None
        now = datetime.now(timezone.utc)
        async with get_connection(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO runs (run_id, workflow_id, status, enable_trsm, task, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, workflow_id, status, 1 if enable_trsm else 0, task, summary_json, now.isoformat()),
            )
            await db.commit()
        return RunRecord(
            run_id=run_id,
            workflow_id=workflow_id,
            status=status,
            enable_trsm=enable_trsm,
            task=task,
            summary=summary,
            created_at=now,
        )

    async def update_run(
        self,
        run_id: str,
        status: str,
        summary: Optional[Dict[str, Any]] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[RunRecord]:
        """Update status and summary of an ongoing or completed run."""
        await self._ensure_db()
        summary_json = json.dumps(summary) if summary else None
        completed_str = (completed_at or datetime.now(timezone.utc)).isoformat() if status in ("completed", "failed", "blocked") else None
        async with get_connection(self.db_path) as db:
            await db.execute(
                """
                UPDATE runs
                SET status = ?, summary = ?, completed_at = ?
                WHERE run_id = ?
                """,
                (status, summary_json, completed_str, run_id),
            )
            await db.commit()
        return await self.get_run(run_id)

    async def get_run(self, run_id: str) -> Optional[RunRecord]:
        """Retrieve a specific run record by run_id."""
        await self._ensure_db()
        async with get_connection(self.db_path) as db:
            cursor = await db.execute(
                "SELECT run_id, workflow_id, status, enable_trsm, task, summary, created_at, completed_at FROM runs WHERE run_id = ?",
                (run_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            summary = json.loads(row["summary"]) if row["summary"] else None
            return RunRecord(
                run_id=row["run_id"],
                workflow_id=row["workflow_id"],
                status=row["status"],
                enable_trsm=bool(row["enable_trsm"]),
                task=row["task"],
                summary=summary,
            )

    async def list_runs(self, limit: int = 50) -> List[RunRecord]:
        """List recent execution runs."""
        await self._ensure_db()
        async with get_connection(self.db_path) as db:
            cursor = await db.execute(
                "SELECT run_id, workflow_id, status, enable_trsm, task, summary, created_at, completed_at FROM runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                summary = json.loads(row["summary"]) if row["summary"] else None
                results.append(
                    RunRecord(
                        run_id=row["run_id"],
                        workflow_id=row["workflow_id"],
                        status=row["status"],
                        enable_trsm=bool(row["enable_trsm"]),
                        task=row["task"],
                        summary=summary,
                    )
                )
            return results
