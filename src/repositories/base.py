"""
Base repository implementations.

Provides abstract base class and JSON file-based implementation.
"""

import json
import os
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type, Callable
import logging

from src.core.models.base import BaseModel, Entity
from src.core.exceptions import NotFoundError, AlreadyExistsError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Entity)


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository.

    Defines the interface for all repositories.
    """

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Get all entities."""
        pass

    @abstractmethod
    def find(self, **criteria) -> List[T]:
        """Find entities matching criteria."""
        pass

    @abstractmethod
    def find_one(self, **criteria) -> Optional[T]:
        """Find single entity matching criteria."""
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity."""
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update existing entity."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        pass

    @abstractmethod
    def count(self, **criteria) -> int:
        """Count entities matching criteria."""
        pass


class JSONRepository(BaseRepository[T]):
    """
    JSON file-based repository implementation.

    Thread-safe implementation for development and small-scale deployments.
    For production, replace with database-backed implementations.
    """

    def __init__(
        self,
        data_dir: str,
        filename: str,
        entity_class: Type[T],
        id_field: str = "id"
    ):
        """
        Initialize JSON repository.

        Args:
            data_dir: Directory to store JSON files
            filename: JSON file name
            entity_class: Pydantic model class for entities
            id_field: Name of the ID field
        """
        self.data_dir = Path(data_dir)
        self.filename = filename
        self.entity_class = entity_class
        self.id_field = id_field
        self.file_path = self.data_dir / filename

        # Thread safety
        self._lock = threading.RLock()

        # Ensure directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize file if not exists
        if not self.file_path.exists():
            self._write_data([])

        logger.debug(f"Initialized JSONRepository: {self.file_path}")

    def _read_data(self) -> List[Dict[str, Any]]:
        """Read data from JSON file."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in {self.file_path}, returning empty list")
            return []
        except FileNotFoundError:
            return []

    def _write_data(self, data: List[Dict[str, Any]]) -> None:
        """Write data to JSON file."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def _to_entity(self, data: Dict[str, Any]) -> T:
        """Convert dictionary to entity."""
        return self.entity_class.model_validate(data)

    def _to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return entity.model_dump(mode="json")

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        with self._lock:
            data = self._read_data()
            for item in data:
                if item.get(self.id_field) == entity_id:
                    return self._to_entity(item)
            return None

    def get_all(self) -> List[T]:
        """Get all entities."""
        with self._lock:
            data = self._read_data()
            return [self._to_entity(item) for item in data]

    def find(self, **criteria) -> List[T]:
        """
        Find entities matching criteria.

        Args:
            **criteria: Field-value pairs to match

        Returns:
            List of matching entities
        """
        with self._lock:
            data = self._read_data()
            results = []

            for item in data:
                match = True
                for key, value in criteria.items():
                    if key not in item:
                        match = False
                        break

                    item_value = item[key]

                    # Handle list membership
                    if isinstance(value, list):
                        if item_value not in value:
                            match = False
                            break
                    # Handle callable predicates
                    elif callable(value):
                        if not value(item_value):
                            match = False
                            break
                    # Direct comparison
                    elif item_value != value:
                        match = False
                        break

                if match:
                    results.append(self._to_entity(item))

            return results

    def find_one(self, **criteria) -> Optional[T]:
        """Find single entity matching criteria."""
        results = self.find(**criteria)
        return results[0] if results else None

    def create(self, entity: T) -> T:
        """Create new entity."""
        with self._lock:
            data = self._read_data()
            entity_id = getattr(entity, self.id_field)

            # Check for duplicate
            for item in data:
                if item.get(self.id_field) == entity_id:
                    raise AlreadyExistsError(
                        self.entity_class.__name__,
                        entity_id
                    )

            data.append(self._to_dict(entity))
            self._write_data(data)

            logger.debug(f"Created {self.entity_class.__name__}: {entity_id}")
            return entity

    def update(self, entity: T) -> T:
        """Update existing entity."""
        with self._lock:
            data = self._read_data()
            entity_id = getattr(entity, self.id_field)
            entity.touch()  # Update timestamp

            for i, item in enumerate(data):
                if item.get(self.id_field) == entity_id:
                    data[i] = self._to_dict(entity)
                    self._write_data(data)
                    logger.debug(f"Updated {self.entity_class.__name__}: {entity_id}")
                    return entity

            raise NotFoundError(self.entity_class.__name__, entity_id)

    def save(self, entity: T) -> T:
        """Save entity (create or update)."""
        entity_id = getattr(entity, self.id_field)
        if self.exists(entity_id):
            return self.update(entity)
        return self.create(entity)

    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        with self._lock:
            data = self._read_data()
            initial_count = len(data)

            data = [item for item in data if item.get(self.id_field) != entity_id]

            if len(data) < initial_count:
                self._write_data(data)
                logger.debug(f"Deleted {self.entity_class.__name__}: {entity_id}")
                return True

            return False

    def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        return self.get_by_id(entity_id) is not None

    def count(self, **criteria) -> int:
        """Count entities matching criteria."""
        if not criteria:
            with self._lock:
                return len(self._read_data())
        return len(self.find(**criteria))

    def clear(self) -> None:
        """Clear all entities (use with caution)."""
        with self._lock:
            self._write_data([])
            logger.warning(f"Cleared all data in {self.file_path}")

    # =====================
    # Pagination Support
    # =====================

    def find_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        **criteria
    ) -> Dict[str, Any]:
        """
        Find entities with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            sort_by: Field to sort by
            sort_desc: Sort descending
            **criteria: Filter criteria

        Returns:
            Dict with items, total, page, page_size, total_pages
        """
        entities = self.find(**criteria)

        # Sort
        if sort_by:
            entities.sort(
                key=lambda x: getattr(x, sort_by, None) or "",
                reverse=sort_desc
            )

        total = len(entities)
        total_pages = (total + page_size - 1) // page_size

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        items = entities[start:end]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }


class CachedRepository(BaseRepository[T]):
    """
    Cached repository decorator.

    Wraps another repository with in-memory caching.
    """

    def __init__(
        self,
        repository: BaseRepository[T],
        cache_ttl: int = 300  # 5 minutes
    ):
        self._repo = repository
        self._cache: Dict[str, tuple] = {}  # id -> (entity, expiry)
        self._cache_ttl = cache_ttl
        self._lock = threading.RLock()

    def _is_valid(self, cache_entry: tuple) -> bool:
        """Check if cache entry is still valid."""
        _, expiry = cache_entry
        return datetime.utcnow().timestamp() < expiry

    def _set_cache(self, entity_id: str, entity: T) -> None:
        """Set cache entry."""
        expiry = datetime.utcnow().timestamp() + self._cache_ttl
        self._cache[entity_id] = (entity, expiry)

    def _invalidate(self, entity_id: str) -> None:
        """Invalidate cache entry."""
        self._cache.pop(entity_id, None)

    def get_by_id(self, entity_id: str) -> Optional[T]:
        with self._lock:
            if entity_id in self._cache and self._is_valid(self._cache[entity_id]):
                return self._cache[entity_id][0]

            entity = self._repo.get_by_id(entity_id)
            if entity:
                self._set_cache(entity_id, entity)
            return entity

    def get_all(self) -> List[T]:
        return self._repo.get_all()

    def find(self, **criteria) -> List[T]:
        return self._repo.find(**criteria)

    def find_one(self, **criteria) -> Optional[T]:
        return self._repo.find_one(**criteria)

    def create(self, entity: T) -> T:
        result = self._repo.create(entity)
        self._set_cache(getattr(result, "id"), result)
        return result

    def update(self, entity: T) -> T:
        result = self._repo.update(entity)
        self._set_cache(getattr(result, "id"), result)
        return result

    def delete(self, entity_id: str) -> bool:
        self._invalidate(entity_id)
        return self._repo.delete(entity_id)

    def exists(self, entity_id: str) -> bool:
        return self._repo.exists(entity_id)

    def count(self, **criteria) -> int:
        return self._repo.count(**criteria)
