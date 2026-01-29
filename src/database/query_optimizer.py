"""
Query Optimizer.

Advanced query optimization utilities for SQLAlchemy.
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Query, Session, joinedload, selectinload, subqueryload
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class QueryStats:
    """Query execution statistics."""
    query: str
    duration_ms: float
    rows_affected: int
    timestamp: float = field(default_factory=time.time)
    explain_plan: Optional[str] = None


class QueryProfiler:
    """
    Query profiler for monitoring and optimization.

    Tracks query execution times and identifies slow queries.
    """

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        self.slow_query_threshold = slow_query_threshold_ms
        self._stats: List[QueryStats] = []
        self._enabled = False

    def enable(self, engine: Engine) -> None:
        """Enable query profiling."""
        if self._enabled:
            return

        @event.listens_for(engine, "before_cursor_execute")
        def before_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault("query_start_time", []).append(time.time())

        @event.listens_for(engine, "after_cursor_execute")
        def after_execute(conn, cursor, statement, parameters, context, executemany):
            start_time = conn.info["query_start_time"].pop(-1)
            duration = (time.time() - start_time) * 1000

            stats = QueryStats(
                query=statement[:500],  # Truncate long queries
                duration_ms=duration,
                rows_affected=cursor.rowcount
            )
            self._stats.append(stats)

            # Log slow queries
            if duration > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected ({duration:.2f}ms): {statement[:200]}..."
                )

        self._enabled = True
        logger.info("Query profiler enabled")

    def disable(self) -> None:
        """Disable query profiling."""
        self._enabled = False

    def get_stats(self, limit: int = 100) -> List[QueryStats]:
        """Get recent query statistics."""
        return self._stats[-limit:]

    def get_slow_queries(self, threshold_ms: Optional[float] = None) -> List[QueryStats]:
        """Get slow queries above threshold."""
        threshold = threshold_ms or self.slow_query_threshold
        return [s for s in self._stats if s.duration_ms > threshold]

    def get_summary(self) -> Dict[str, Any]:
        """Get profiling summary."""
        if not self._stats:
            return {"total_queries": 0}

        durations = [s.duration_ms for s in self._stats]

        return {
            "total_queries": len(self._stats),
            "total_time_ms": sum(durations),
            "avg_time_ms": sum(durations) / len(durations),
            "max_time_ms": max(durations),
            "min_time_ms": min(durations),
            "slow_queries": len(self.get_slow_queries()),
        }

    def clear(self) -> None:
        """Clear statistics."""
        self._stats.clear()


# Singleton profiler
query_profiler = QueryProfiler()


class QueryBuilder:
    """
    Fluent query builder with optimization hints.

    Provides a clean interface for building optimized queries.
    """

    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session
        self._query = session.query(model)
        self._eager_loads: List = []
        self._filters: List = []
        self._order_by: List = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None

    def filter(self, *criteria) -> "QueryBuilder":
        """Add filter criteria."""
        self._filters.extend(criteria)
        return self

    def filter_by(self, **kwargs) -> "QueryBuilder":
        """Add filter by keyword arguments."""
        self._query = self._query.filter_by(**kwargs)
        return self

    def eager_load(self, *relationships, strategy: str = "joined") -> "QueryBuilder":
        """
        Add eager loading for relationships.

        Args:
            relationships: Relationship names to load
            strategy: 'joined', 'subquery', or 'selectin'
        """
        loader_map = {
            "joined": joinedload,
            "subquery": subqueryload,
            "selectin": selectinload,
        }
        loader = loader_map.get(strategy, joinedload)

        for rel in relationships:
            self._eager_loads.append(loader(rel))

        return self

    def order_by(self, *columns) -> "QueryBuilder":
        """Add ordering."""
        self._order_by.extend(columns)
        return self

    def limit(self, limit: int) -> "QueryBuilder":
        """Set result limit."""
        self._limit = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder":
        """Set result offset."""
        self._offset = offset
        return self

    def paginate(self, page: int, per_page: int = 20) -> "QueryBuilder":
        """Add pagination."""
        self._limit = per_page
        self._offset = (page - 1) * per_page
        return self

    def build(self) -> Query:
        """Build the final query."""
        query = self._query

        # Apply eager loads
        for load in self._eager_loads:
            query = query.options(load)

        # Apply filters
        for f in self._filters:
            query = query.filter(f)

        # Apply ordering
        for o in self._order_by:
            query = query.order_by(o)

        # Apply limit and offset
        if self._limit:
            query = query.limit(self._limit)
        if self._offset:
            query = query.offset(self._offset)

        return query

    def all(self) -> List[T]:
        """Execute query and return all results."""
        return self.build().all()

    def first(self) -> Optional[T]:
        """Execute query and return first result."""
        return self.build().first()

    def one(self) -> T:
        """Execute query and return exactly one result."""
        return self.build().one()

    def one_or_none(self) -> Optional[T]:
        """Execute query and return one result or None."""
        return self.build().one_or_none()

    def count(self) -> int:
        """Get count of results."""
        return self.build().count()

    def exists(self) -> bool:
        """Check if any results exist."""
        return self.session.query(self.build().exists()).scalar()


class BulkOperations:
    """
    Bulk database operations for performance.

    Provides efficient batch insert/update/delete.
    """

    def __init__(self, session: Session):
        self.session = session

    def bulk_insert(
        self,
        model: Type[T],
        data: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """
        Bulk insert records.

        Args:
            model: SQLAlchemy model class
            data: List of dictionaries with data
            batch_size: Number of records per batch

        Returns:
            Number of inserted records
        """
        total = 0

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            self.session.bulk_insert_mappings(model, batch)
            self.session.flush()
            total += len(batch)

        self.session.commit()
        logger.info(f"Bulk inserted {total} records into {model.__tablename__}")

        return total

    def bulk_update(
        self,
        model: Type[T],
        data: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """
        Bulk update records.

        Each dict must include the primary key.

        Args:
            model: SQLAlchemy model class
            data: List of dictionaries with data
            batch_size: Number of records per batch

        Returns:
            Number of updated records
        """
        total = 0

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            self.session.bulk_update_mappings(model, batch)
            self.session.flush()
            total += len(batch)

        self.session.commit()
        logger.info(f"Bulk updated {total} records in {model.__tablename__}")

        return total

    def bulk_upsert(
        self,
        model: Type[T],
        data: List[Dict[str, Any]],
        unique_columns: List[str],
        batch_size: int = 1000
    ) -> Dict[str, int]:
        """
        Bulk upsert (insert or update).

        Args:
            model: SQLAlchemy model class
            data: List of dictionaries with data
            unique_columns: Columns to check for conflicts
            batch_size: Number of records per batch

        Returns:
            Dict with inserted and updated counts
        """
        from sqlalchemy.dialects.postgresql import insert

        inserted = 0
        updated = 0

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]

            stmt = insert(model).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=unique_columns,
                set_={c: stmt.excluded[c] for c in batch[0].keys() if c not in unique_columns}
            )

            result = self.session.execute(stmt)
            self.session.flush()

            # Note: This is an approximation
            inserted += len(batch)

        self.session.commit()
        logger.info(f"Bulk upserted {inserted} records in {model.__tablename__}")

        return {"inserted": inserted, "updated": updated}

    def bulk_delete(
        self,
        model: Type[T],
        ids: List[Any],
        id_column: str = "id",
        batch_size: int = 1000
    ) -> int:
        """
        Bulk delete records by IDs.

        Args:
            model: SQLAlchemy model class
            ids: List of IDs to delete
            id_column: Name of ID column
            batch_size: Number of records per batch

        Returns:
            Number of deleted records
        """
        total = 0
        id_attr = getattr(model, id_column)

        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            deleted = self.session.query(model).filter(
                id_attr.in_(batch)
            ).delete(synchronize_session=False)
            self.session.flush()
            total += deleted

        self.session.commit()
        logger.info(f"Bulk deleted {total} records from {model.__tablename__}")

        return total


def with_retry(
    max_retries: int = 3,
    retry_on: tuple = (Exception,),
    delay: float = 0.5
):
    """
    Decorator for retrying database operations.

    Args:
        max_retries: Maximum number of retry attempts
        retry_on: Tuple of exceptions to retry on
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                        )
                        await asyncio.sleep(delay * (attempt + 1))

            raise last_error

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                        )
                        time.sleep(delay * (attempt + 1))

            raise last_error

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


@contextmanager
def timed_query(description: str = "Query"):
    """
    Context manager for timing queries.

    Usage:
        with timed_query("Fetch users"):
            users = session.query(User).all()
    """
    start = time.time()
    try:
        yield
    finally:
        duration = (time.time() - start) * 1000
        logger.info(f"{description} completed in {duration:.2f}ms")


def explain_query(session: Session, query: Query) -> str:
    """
    Get EXPLAIN ANALYZE output for a query.

    Args:
        session: Database session
        query: SQLAlchemy query

    Returns:
        EXPLAIN ANALYZE output
    """
    statement = query.statement.compile(
        compile_kwargs={"literal_binds": True}
    )

    explain = session.execute(
        text(f"EXPLAIN ANALYZE {statement}")
    )

    return "\n".join(row[0] for row in explain)


def create_indexes_sql(table_name: str, indexes: List[Dict]) -> List[str]:
    """
    Generate CREATE INDEX SQL statements.

    Args:
        table_name: Name of the table
        indexes: List of index definitions

    Index definition format:
        {
            "name": "idx_users_email",
            "columns": ["email"],
            "unique": False,
            "using": "btree"  # btree, hash, gin, gist
        }

    Returns:
        List of SQL statements
    """
    statements = []

    for idx in indexes:
        unique = "UNIQUE " if idx.get("unique") else ""
        using = idx.get("using", "btree")
        columns = ", ".join(idx["columns"])

        sql = (
            f"CREATE {unique}INDEX IF NOT EXISTS {idx['name']} "
            f"ON {table_name} USING {using} ({columns})"
        )
        statements.append(sql)

    return statements
