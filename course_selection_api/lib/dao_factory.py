import asyncio
from contextlib import asynccontextmanager
from functools import wraps
from typing import List, Optional, Type

import asyncpg
from pydantic import BaseModel


class DatabaseSettings(BaseModel):
    host: str
    username: str
    password: str
    database: str
    port: int


class BaseDao:

    def __init__(self, connection: asyncpg.Connection, operator: Optional[str]):
        self._connection = connection
        self._operator = operator

    @property
    def connection(self) -> asyncpg.Connection:
        return self._connection

    @property
    def operator(self) -> str:
        return self._operator


class DaoFactory:

    def __init__(self, host: str,
                 username: str,
                 password: str,
                 database: str,
                 port: int = 5432):
        self._settings = DatabaseSettings(host=host, username=username, password=password, database=database, port=port)

    async def _get_connection(self) -> asyncpg.Connection:
        return await asyncpg.connect(host=self._settings.host, user=self._settings.username,
                                     password=self._settings.password, database=self._settings.database,
                                     port=self._settings.port)

    @asynccontextmanager
    async def create_daos(self, *dao_classes: List[Type[BaseDao]], operator: str = None, transaction: bool = False) -> \
            List[BaseDao]:
        connection = await self._get_connection()
        daos = [dao_class(connection, operator)
                for dao_class in dao_classes]
        try:
            if transaction:
                async with connection.transaction():
                    yield daos
            else:
                yield daos
        finally:
            await asyncio.gather(connection.close(timeout=10), return_exceptions=True)


def default_connection(dao_factory: DaoFactory):
    def decorator(func):
        @wraps(func)
        async def auto_create_connection(*args, **kwargs):
            for arg in args:
                if isinstance(arg, asyncpg.Connection):
                    return await func(*args, **kwargs)
            for kwarg in kwargs.values():
                if isinstance(kwarg, asyncpg.Connection):
                    return await func(*args, **kwargs)
            connection = await dao_factory._get_connection()
            try:
                return await func(connection=connection, *args, **kwargs)
            finally:
                await asyncio.gather(connection.close(timeout=10), return_exceptions=True)

        return auto_create_connection

    return decorator
