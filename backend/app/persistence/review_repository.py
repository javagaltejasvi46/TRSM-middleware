"""Repository for Human-in-the-Loop review states in SQLite."""

from datetime import datetime, timezone
from typing import List, Optional
from .db import get_connection, init_db
from .models import ReviewRecord


class ReviewRepository:
    """Provides SQLite persistence for Human-in-the-Loop reviews."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    async def _ensure_db(self):
        await init_db(self.db_path)

    async def create_review(
        self,
        review_id: str,
        run_id: str,
        trace_id: str,
        event_id: str,
        actor_id: str,
        action_type: str,
        target: str,
    ) -> ReviewRecord:
        """Create a pending review record."""
        await self._ensure_db()
        now = datetime.now(timezone.utc)
        async with get_connection(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO reviews (
                    review_id, run_id, trace_id, event_id, actor_id, action_type, target, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (review_id, run_id, trace_id, event_id, actor_id, action_type, target, now.isoformat()),
            )
            await db.commit()
        return ReviewRecord(
            review_id=review_id,
            run_id=run_id,
            trace_id=trace_id,
            event_id=event_id,
            actor_id=actor_id,
            action_type=action_type,
            target=target,
            status="pending",
            created_at=now,
        )

    async def get_review(self, review_id: str) -> Optional[ReviewRecord]:
        """Retrieve a review by ID."""
        await self._ensure_db()
        async with get_connection(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM reviews WHERE review_id = ?",
                (review_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return ReviewRecord(
                review_id=row["review_id"],
                run_id=row["run_id"],
                trace_id=row["trace_id"],
                event_id=row["event_id"],
                actor_id=row["actor_id"],
                action_type=row["action_type"],
                target=row["target"],
                status=row["status"],
                decision=row["decision"],
                reviewer_comment=row["reviewer_comment"],
            )

    async def list_pending_reviews(self) -> List[ReviewRecord]:
        """List all pending reviews."""
        await self._ensure_db()
        async with get_connection(self.db_path) as db:
            cursor = await db.execute("SELECT * FROM reviews WHERE status = 'pending' ORDER BY created_at ASC")
            rows = await cursor.fetchall()
            return [
                ReviewRecord(
                    review_id=row["review_id"],
                    run_id=row["run_id"],
                    trace_id=row["trace_id"],
                    event_id=row["event_id"],
                    actor_id=row["actor_id"],
                    action_type=row["action_type"],
                    target=row["target"],
                    status=row["status"],
                    decision=row["decision"],
                    reviewer_comment=row["reviewer_comment"],
                )
                for row in rows
            ]

    async def resolve_review(
        self,
        review_id: str,
        decision: str,
        comment: str,
    ) -> Optional[ReviewRecord]:
        """Resolve a pending review."""
        await self._ensure_db()
        now = datetime.now(timezone.utc)
        async with get_connection(self.db_path) as db:
            cursor = await db.execute(
                """
                UPDATE reviews
                SET status = 'resolved', decision = ?, reviewer_comment = ?, resolved_at = ?
                WHERE review_id = ?
                """,
                (decision, comment, now.isoformat(), review_id),
            )
            await db.commit()
            if cursor.rowcount == 0:
                return None
        return await self.get_review(review_id)
