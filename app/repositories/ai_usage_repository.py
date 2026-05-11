from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import desc, func

from app.models.tables import AIUsageLog
from app.repositories.utils import SQLAlchemyRepository, model_to_dict


@dataclass
class AIUsageLogRecord:
    feature: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    video_id: int | None = None


class AIUsageRepository(SQLAlchemyRepository):
    def __init__(self, db_path: str | Path | None = None) -> None:
        super().__init__(db_path)

    def log_usage(self, record: AIUsageLogRecord) -> dict:
        payload = asdict(record)
        with self._session() as session:
            row = AIUsageLog(
                feature=payload["feature"],
                provider=payload["provider"],
                model=payload["model"],
                input_tokens=payload["input_tokens"],
                output_tokens=payload["output_tokens"],
                estimated_cost_usd=payload["estimated_cost_usd"],
                video_id=payload["video_id"],
            )
            session.add(row)
            session.flush()
            session.refresh(row)
            return model_to_dict(row)

    @staticmethod
    def _build_date_clause(start_date: str | None, end_date: str | None) -> tuple[str, list[object]]:
        clauses = []
        params: list[object] = []
        if start_date:
            clauses.append("date(created_at) >= date(?)")
            params.append(start_date)
        if end_date:
            clauses.append("date(created_at) <= date(?)")
            params.append(end_date)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where, params

    @staticmethod
    def _project_monthly(total_cost: float, start_date: str | None, end_date: str | None, active_days: int) -> float:
        if total_cost <= 0:
            return 0.0
        if active_days > 0:
            span_days = active_days
        elif start_date and end_date:
            try:
                start = date.fromisoformat(start_date)
                end = date.fromisoformat(end_date)
                span_days = max((end - start).days + 1, 1)
            except ValueError:
                span_days = 1
        else:
            span_days = 1
        return round((total_cost / span_days) * 30, 6)

    @staticmethod
    def _apply_date_filters(query, start_date: str | None, end_date: str | None):
        created_on = func.date(AIUsageLog.created_at)
        if start_date:
            query = query.filter(created_on >= start_date)
        if end_date:
            query = query.filter(created_on <= end_date)
        return query

    def get_summary(self, start_date: str | None = None, end_date: str | None = None) -> dict:
        with self._session() as session:
            query = session.query(
                func.count(AIUsageLog.id).label("total_calls"),
                func.coalesce(func.sum(AIUsageLog.input_tokens), 0).label("total_input_tokens"),
                func.coalesce(func.sum(AIUsageLog.output_tokens), 0).label("total_output_tokens"),
                func.coalesce(func.sum(AIUsageLog.estimated_cost_usd), 0.0).label("total_estimated_cost_usd"),
                func.count(func.distinct(func.date(AIUsageLog.created_at))).label("active_days"),
            )
            row = self._apply_date_filters(query, start_date, end_date).one()
        payload = {
            "total_calls": int(row.total_calls or 0),
            "total_input_tokens": int(row.total_input_tokens or 0),
            "total_output_tokens": int(row.total_output_tokens or 0),
            "total_estimated_cost_usd": float(row.total_estimated_cost_usd or 0.0),
            "active_days": int(row.active_days or 0),
        }
        payload["start_date"] = start_date
        payload["end_date"] = end_date
        payload["projected_monthly_cost_usd"] = self._project_monthly(
            float(payload["total_estimated_cost_usd"] or 0.0),
            start_date,
            end_date,
            int(payload.get("active_days", 0) or 0),
        )
        return payload

    def get_usage_by_feature(self, start_date: str | None = None, end_date: str | None = None) -> list[dict]:
        with self._session() as session:
            query = session.query(
                AIUsageLog.feature.label("feature"),
                AIUsageLog.provider.label("provider"),
                func.count(AIUsageLog.id).label("total_calls"),
                func.coalesce(func.sum(AIUsageLog.input_tokens), 0).label("total_input_tokens"),
                func.coalesce(func.sum(AIUsageLog.output_tokens), 0).label("total_output_tokens"),
                func.coalesce(func.sum(AIUsageLog.estimated_cost_usd), 0.0).label("total_estimated_cost_usd"),
                func.count(func.distinct(func.date(AIUsageLog.created_at))).label("active_days"),
            )
            rows = (
                self._apply_date_filters(query, start_date, end_date)
                .group_by(AIUsageLog.feature, AIUsageLog.provider)
                .order_by(
                    desc("total_estimated_cost_usd"),
                    desc("total_calls"),
                    AIUsageLog.feature.asc(),
                )
                .all()
            )
        items = []
        for row in rows:
            payload = {
                "feature": row.feature,
                "provider": row.provider,
                "total_calls": int(row.total_calls or 0),
                "total_input_tokens": int(row.total_input_tokens or 0),
                "total_output_tokens": int(row.total_output_tokens or 0),
                "total_estimated_cost_usd": float(row.total_estimated_cost_usd or 0.0),
                "active_days": int(row.active_days or 0),
            }
            payload["start_date"] = start_date
            payload["end_date"] = end_date
            payload["projected_monthly_cost_usd"] = self._project_monthly(
                float(payload["total_estimated_cost_usd"] or 0.0),
                start_date,
                end_date,
                int(payload.get("active_days", 0) or 0),
            )
            items.append(payload)
        return items
