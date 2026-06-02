"""DI do alert-service."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from alert_service.repositories import AlertRepository
from alert_service.services import AlertService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db = request.app.state.database
    async for session in db.session():
        yield session


def get_alert_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> AlertService:
    return AlertService(
        alerts=AlertRepository(session),
        rule_engine=request.app.state.rule_engine,
        event_bus=request.app.state.event_bus,
    )
