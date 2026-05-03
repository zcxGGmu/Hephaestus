"""
PostgreSQL connection and lightweight query builder utilities.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict, List, Optional, Union

import asyncpg  # type: ignore

from utils.config import config
from utils.logger import logger


class DBConnection:
    """Thread-safe singleton for the asyncpg connection pool."""

    _instance: Optional["DBConnection"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._pool = None
        return cls._instance

    def __init__(self):
        """Keep construction cheap; pool creation happens in initialize()."""
        pass

    async def initialize(self):
        """Initialize the PostgreSQL connection pool once."""
        if self._initialized:
            return

        database_url = os.getenv("DATABASE_URL")
        if not database_url and hasattr(config, "DATABASE_URL"):
            database_url = config.DATABASE_URL
        if not database_url:
            database_url = "postgresql://postgres@localhost:5432/hephaestus"

        try:
            self._pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=10,
                command_timeout=60,
            )
            self._initialized = True
            logger.debug("PostgreSQL connection pool initialized")
        except Exception as exc:
            logger.error(f"PostgreSQL connection pool initialization error: {exc}")
            raise RuntimeError(
                f"PostgreSQL connection pool initialization failed: {exc}"
            ) from exc

    @property
    async def client(self):
        """Return a query-capable client wrapper."""
        if not self._initialized:
            await self.initialize()
        return PostgreSQLClient(self._pool)

    @classmethod
    async def disconnect(cls):
        """Close the PostgreSQL connection pool."""
        if cls._instance and cls._instance._pool:
            await cls._instance._pool.close()
            cls._instance._pool = None
            cls._instance._initialized = False
            logger.info("PostgreSQL connection pool closed")


class PostgreSQLClient:
    """Small wrapper that mimics the supabase-style API used in this repo."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    def table(self, table_name: str):
        return PostgreSQLTable(self.pool, table_name)

    def schema(self, schema_name: str):
        return PostgreSQLSchema(self.pool, schema_name)


class PostgreSQLSchema:
    def __init__(self, pool: asyncpg.Pool, schema_name: str):
        self.pool = pool
        self.schema_name = schema_name

    def table(self, table_name: str):
        return PostgreSQLTable(self.pool, f"{self.schema_name}.{table_name}")


class PostgreSQLTable:
    def __init__(self, pool: asyncpg.Pool, table_name: str):
        self.pool = pool
        self.table_name = table_name
        self._select_fields = "*"
        self._where_conditions: List[str] = []
        self._order_by: List[str] = []
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None
        self._count_flag = False
        self._params: List[Any] = []
        self._single_result = False
        self._maybe_single = False

    def select(self, fields: str = "*", count: str = None):
        self._select_fields = fields
        if count == "exact":
            self._count_flag = True
        return self

    def eq(self, column: str, value: Any):
        self._where_conditions.append(f"{column} = ${len(self._params) + 1}")
        self._params.append(value)
        return self

    def neq(self, column: str, value: Any):
        if value is None:
            self._where_conditions.append(f"{column} IS NOT NULL")
        else:
            self._where_conditions.append(f"{column} != ${len(self._params) + 1}")
            self._params.append(value)
        return self

    def lt(self, column: str, value: Any):
        self._where_conditions.append(f"{column} < ${len(self._params) + 1}")
        self._params.append(value)
        return self

    def gt(self, column: str, value: Any):
        self._where_conditions.append(f"{column} > ${len(self._params) + 1}")
        self._params.append(value)
        return self

    def gte(self, column: str, value: Any):
        self._where_conditions.append(f"{column} >= ${len(self._params) + 1}")
        self._params.append(value)
        return self

    def lte(self, column: str, value: Any):
        self._where_conditions.append(f"{column} <= ${len(self._params) + 1}")
        self._params.append(value)
        return self

    def like(self, column: str, pattern: str):
        self._where_conditions.append(f"{column} LIKE ${len(self._params) + 1}")
        self._params.append(pattern)
        return self

    def ilike(self, column: str, pattern: str):
        self._where_conditions.append(f"{column} ILIKE ${len(self._params) + 1}")
        self._params.append(pattern)
        return self

    def contains(self, column: str, value: Any):
        if isinstance(value, list):
            self._where_conditions.append(f"{column} @> ${len(self._params) + 1}")
            self._params.append(json.dumps(value))
        else:
            self._where_conditions.append(f"{column} LIKE ${len(self._params) + 1}")
            self._params.append(f"%{value}%")
        return self

    def in_(self, column: str, values: List[Any]):
        if not values:
            self._where_conditions.append("1 = 0")
            return self

        placeholders = []
        for value in values:
            self._params.append(value)
            placeholders.append(f"${len(self._params)}")
        self._where_conditions.append(f"{column} IN ({', '.join(placeholders)})")
        return self

    def is_(self, column: str, value: Any):
        if value is None:
            self._where_conditions.append(f"{column} IS NULL")
        else:
            self._where_conditions.append(f"{column} IS ${len(self._params) + 1}")
            self._params.append(value)
        return self

    @property
    def not_(self):
        return PostgreSQLNotBuilder(self)

    def filter(self, field_expression: str, operator: str, value: Any):
        if operator == "eq":
            return self.eq(field_expression, value)
        if operator == "neq":
            return self.neq(field_expression, value)
        if operator == "lt":
            return self.lt(field_expression, value)
        if operator == "gt":
            return self.gt(field_expression, value)
        if "->>" in field_expression:
            self._where_conditions.append(
                f"{field_expression} = ${len(self._params) + 1}"
            )
            self._params.append(value)
            return self
        logger.warning(f"Unsupported filter operator: {operator}")
        return self

    def or_(self, condition: str):
        if "ilike" not in condition:
            return self

        parts = condition.split(",")
        or_conditions = []
        for part in parts:
            if ".ilike." in part:
                field, _, pattern = part.split(".", 2)
                or_conditions.append(f"{field} ILIKE ${len(self._params) + 1}")
                self._params.append(pattern)

        if or_conditions:
            self._where_conditions.append(f"({' OR '.join(or_conditions)})")
        return self

    def order(self, column: str, desc: bool = False):
        direction = "DESC" if desc else "ASC"
        self._order_by.append(f"{column} {direction}")
        return self

    def range(self, start: int, end: int):
        self._limit_value = end - start + 1
        self._offset_value = start
        return self

    def limit(self, count: int):
        self._limit_value = count
        return self

    def single(self):
        self._single_result = True
        self._limit_value = 1
        return self

    def maybe_single(self):
        self._maybe_single = True
        self._limit_value = 1
        return self

    async def execute(self):
        query_parts = [f"SELECT {self._select_fields}", f"FROM {self.table_name}"]

        count_query = None
        if self._count_flag:
            count_query = f"SELECT COUNT(*) FROM {self.table_name}"
            if self._where_conditions:
                count_query += f" WHERE {' AND '.join(self._where_conditions)}"

        if self._where_conditions:
            query_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")
        if self._order_by:
            query_parts.append(f"ORDER BY {', '.join(self._order_by)}")
        if self._limit_value is not None:
            query_parts.append(f"LIMIT {self._limit_value}")
        if self._offset_value is not None:
            query_parts.append(f"OFFSET {self._offset_value}")

        query = " ".join(query_parts)

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *self._params)
                data = [dict(row) for row in rows]
                count = None
                if self._count_flag and count_query:
                    count_result = await conn.fetchval(count_query, *self._params)
                    count = int(count_result) if count_result else 0

                if self._single_result:
                    if not data:
                        raise ValueError("Query returned no rows")
                    return QueryResult(data[0], count)
                if self._maybe_single:
                    return QueryResult(data[0] if data else None, count)
                return QueryResult(data, count)
        except Exception as exc:
            logger.error(
                f"Query execution failed: {exc}, SQL: {query}, params: {self._params}"
            )
            raise RuntimeError(f"Database query failed: {exc}") from exc

    async def insert(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]):
        try:
            if isinstance(data, dict):
                data = [data]
            if not data:
                return QueryResult([])

            columns = list(data[0].keys())
            values_placeholders = []
            all_values: List[Any] = []

            for i, record in enumerate(data):
                record_placeholders = []
                for j, column in enumerate(columns):
                    placeholder_index = i * len(columns) + j + 1
                    record_placeholders.append(f"${placeholder_index}")
                    all_values.append(record[column])
                values_placeholders.append(f"({', '.join(record_placeholders)})")

            query = (
                f"INSERT INTO {self.table_name} ({', '.join(columns)}) "
                f"VALUES {', '.join(values_placeholders)} RETURNING *"
            )

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *all_values)
                return QueryResult([dict(row) for row in rows])
        except Exception as exc:
            logger.error(f"Insert operation failed: {exc}")
            raise RuntimeError(f"Database insert failed: {exc}") from exc

    async def update(self, data: Dict[str, Any]):
        try:
            set_clauses = []
            values: List[Any] = []
            for key, value in data.items():
                set_clauses.append(f"{key} = ${len(values) + len(self._params) + 1}")
                values.append(value)

            query_parts = [f"UPDATE {self.table_name}", f"SET {', '.join(set_clauses)}"]
            if self._where_conditions:
                query_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")
            query_parts.append("RETURNING *")
            query = " ".join(query_parts)

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *(self._params + values))
                result_data = [dict(row) for row in rows]
                if self._single_result or self._maybe_single:
                    if not result_data and self._single_result:
                        raise ValueError("Update operation affected no rows")
                    return QueryResult(result_data[0] if result_data else None)
                return QueryResult(result_data)
        except Exception as exc:
            logger.error(f"Update operation failed: {exc}")
            raise RuntimeError(f"Database update failed: {exc}") from exc

    async def delete(self):
        try:
            query_parts = [f"DELETE FROM {self.table_name}"]
            if self._where_conditions:
                query_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")
            query_parts.append("RETURNING *")
            query = " ".join(query_parts)

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *self._params)
                return QueryResult([dict(row) for row in rows])
        except Exception as exc:
            logger.error(f"Delete operation failed: {exc}")
            raise RuntimeError(f"Database delete failed: {exc}") from exc


class PostgreSQLNotBuilder:
    def __init__(self, table_builder: PostgreSQLTable):
        self.table_builder = table_builder

    def is_(self, column: str, value: Any):
        if value is None:
            self.table_builder._where_conditions.append(f"{column} IS NOT NULL")
        else:
            self.table_builder._where_conditions.append(
                f"{column} IS NOT ${len(self.table_builder._params) + 1}"
            )
            self.table_builder._params.append(value)
        return self.table_builder


class QueryResult:
    def __init__(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, Any], None],
        count: Optional[int] = None,
    ):
        self.data = data
        self.count = count
