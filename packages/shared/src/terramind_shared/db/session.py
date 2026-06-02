"""Gerenciador de engine + sessões async do SQLAlchemy."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Wrapper sobre engine async + sessionmaker.

    Cada serviço cria uma única instância no `lifespan` do FastAPI.
    A dependency `get_db_session` consome via `async for session in db.session()`.
    """

    def __init__(
        self,
        url: str,
        *,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
    ) -> None:
        self._engine = create_async_engine(
            url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
            future=True,
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    @property
    def engine(self):  # noqa: ANN201
        return self._engine

    async def session(self) -> AsyncIterator[AsyncSession]:
        """Async generator para uso como dependency do FastAPI.

        Commit automático no sucesso, rollback em qualquer exceção.
        """
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def dispose(self) -> None:
        await self._engine.dispose()
