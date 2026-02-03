"""Deep hierarchy test repo - 5+ level inheritance, mixins, multiple inheritance."""

from abc import ABC, abstractmethod
from typing import Any, Protocol


# ============================================================================
# Level 0: Protocols (structural typing)
# ============================================================================


class Identifiable(Protocol):
    """Protocol for identifiable objects."""

    def get_id(self) -> str:
        """Return unique identifier."""
        ...


class Validatable(Protocol):
    """Protocol for validatable objects."""

    def validate(self) -> bool:
        """Validate the object."""
        ...


class Serializable(Protocol):
    """Protocol for serializable objects."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


# ============================================================================
# Level 1: Abstract Base Classes
# ============================================================================


class BaseEntity(ABC):
    """Abstract base entity (Level 1)."""

    @abstractmethod
    def get_id(self) -> str:
        """Return entity ID."""
        ...

    @abstractmethod
    def validate(self) -> bool:
        """Validate entity."""
        ...

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(id={self.get_id()})"


class Loggable(ABC):
    """Abstract logging mixin (Level 1)."""

    @abstractmethod
    def get_log_prefix(self) -> str:
        """Return log prefix."""
        ...

    def log(self, message: str) -> None:
        """Log a message."""
        print(f"[{self.get_log_prefix()}] {message}")


class Cacheable(ABC):
    """Abstract caching mixin (Level 1)."""

    _cache: dict = {}

    @abstractmethod
    def get_cache_key(self) -> str:
        """Return cache key."""
        ...

    def cache_get(self) -> Any:
        """Get from cache."""
        return self._cache.get(self.get_cache_key())

    def cache_set(self, value: Any) -> None:
        """Set in cache."""
        self._cache[self.get_cache_key()] = value

    def cache_clear(self) -> None:
        """Clear from cache."""
        if self.get_cache_key() in self._cache:
            del self._cache[self.get_cache_key()]


# ============================================================================
# Level 2: Concrete Base Classes
# ============================================================================


class NamedEntity(BaseEntity, Loggable):
    """Named entity with logging (Level 2)."""

    def __init__(self, entity_id: str, name: str):
        """Initialize named entity."""
        self.entity_id = entity_id
        self.name = name

    def get_id(self) -> str:
        """Return entity ID."""
        return self.entity_id

    def validate(self) -> bool:
        """Validate named entity."""
        return bool(self.entity_id and self.name)

    def get_log_prefix(self) -> str:
        """Return log prefix."""
        return f"{self.__class__.__name__}:{self.entity_id}"


class TimestampedEntity(NamedEntity):
    """Entity with timestamps (Level 3 from BaseEntity)."""

    def __init__(self, entity_id: str, name: str):
        """Initialize timestamped entity."""
        super().__init__(entity_id, name)
        self.created_at: str = ""
        self.updated_at: str = ""

    def touch(self) -> None:
        """Update timestamp."""
        from datetime import datetime
        self.updated_at = datetime.now().isoformat()

    def validate(self) -> bool:
        """Validate with timestamp check."""
        return super().validate() and bool(self.created_at)


# ============================================================================
# Level 3: Domain Base Classes
# ============================================================================


class VersionedEntity(TimestampedEntity, Cacheable):
    """Versioned entity with caching (Level 4 from BaseEntity)."""

    def __init__(self, entity_id: str, name: str):
        """Initialize versioned entity."""
        super().__init__(entity_id, name)
        self.version: int = 1

    def get_cache_key(self) -> str:
        """Return cache key."""
        return f"{self.entity_id}:v{self.version}"

    def increment_version(self) -> None:
        """Increment version."""
        self.cache_clear()
        self.version += 1
        self.touch()

    def validate(self) -> bool:
        """Validate with version check."""
        return super().validate() and self.version > 0


class AuditedEntity(VersionedEntity):
    """Audited entity (Level 5 from BaseEntity)."""

    def __init__(self, entity_id: str, name: str, created_by: str):
        """Initialize audited entity."""
        super().__init__(entity_id, name)
        self.created_by = created_by
        self.modified_by: str | None = None
        self.audit_log: list[str] = []

    def record_change(self, user: str, action: str) -> None:
        """Record audit change."""
        self.modified_by = user
        self.audit_log.append(f"{user}: {action}")
        self.increment_version()

    def get_audit_history(self) -> list[str]:
        """Get audit history."""
        return self.audit_log.copy()

    def validate(self) -> bool:
        """Validate with audit check."""
        return super().validate() and bool(self.created_by)


# ============================================================================
# Level 4: Mixins for Cross-Cutting Concerns
# ============================================================================


class TaggableMixin:
    """Mixin for taggable entities."""

    tags: list[str]

    def __init_tags__(self) -> None:
        """Initialize tags."""
        if not hasattr(self, "tags"):
            self.tags = []

    def add_tag(self, tag: str) -> None:
        """Add tag."""
        self.__init_tags__()
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove tag."""
        self.__init_tags__()
        if tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if has tag."""
        self.__init_tags__()
        return tag in self.tags


class SearchableMixin:
    """Mixin for searchable entities."""

    def get_searchable_text(self) -> str:
        """Get searchable text."""
        parts = []
        if hasattr(self, "name"):
            parts.append(self.name)
        if hasattr(self, "description"):
            parts.append(self.description)
        if hasattr(self, "tags"):
            parts.extend(self.tags)
        return " ".join(parts).lower()

    def matches(self, query: str) -> bool:
        """Check if matches query."""
        return query.lower() in self.get_searchable_text()


class NotifiableMixin:
    """Mixin for notifiable entities."""

    subscribers: list[str]

    def __init_subscribers__(self) -> None:
        """Initialize subscribers."""
        if not hasattr(self, "subscribers"):
            self.subscribers = []

    def subscribe(self, subscriber_id: str) -> None:
        """Add subscriber."""
        self.__init_subscribers__()
        if subscriber_id not in self.subscribers:
            self.subscribers.append(subscriber_id)

    def unsubscribe(self, subscriber_id: str) -> None:
        """Remove subscriber."""
        self.__init_subscribers__()
        if subscriber_id in self.subscribers:
            self.subscribers.remove(subscriber_id)

    def notify(self, message: str) -> list[str]:
        """Notify all subscribers."""
        self.__init_subscribers__()
        return [f"Notifying {s}: {message}" for s in self.subscribers]


# ============================================================================
# Level 5: Concrete Domain Classes (deepest level)
# ============================================================================


class Document(AuditedEntity, TaggableMixin, SearchableMixin):
    """Document with full features (Level 6 from BaseEntity)."""

    def __init__(self, doc_id: str, title: str, created_by: str, content: str = ""):
        """Initialize document."""
        super().__init__(doc_id, title, created_by)
        self.content = content
        self.description = ""
        self.tags = []

    def update_content(self, user: str, new_content: str) -> None:
        """Update document content."""
        self.content = new_content
        self.record_change(user, "content_updated")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.get_id(),
            "title": self.name,
            "content": self.content,
            "version": self.version,
            "tags": self.tags,
        }

    def validate(self) -> bool:
        """Validate document."""
        return super().validate() and len(self.content) > 0


class Task(AuditedEntity, TaggableMixin, NotifiableMixin):
    """Task with notifications (Level 6 from BaseEntity)."""

    def __init__(self, task_id: str, title: str, created_by: str, assignee: str | None = None):
        """Initialize task."""
        super().__init__(task_id, title, created_by)
        self.assignee = assignee
        self.status = "pending"
        self.tags = []
        self.subscribers = []

    def assign_to(self, user: str, assigned_by: str) -> None:
        """Assign task to user."""
        self.assignee = user
        self.record_change(assigned_by, f"assigned_to:{user}")
        self.notify(f"Task assigned to {user}")

    def complete(self, completed_by: str) -> None:
        """Mark task complete."""
        self.status = "completed"
        self.record_change(completed_by, "completed")
        self.notify("Task completed")

    def validate(self) -> bool:
        """Validate task."""
        return super().validate() and self.status in ("pending", "in_progress", "completed")


class Project(AuditedEntity, TaggableMixin, SearchableMixin, NotifiableMixin):
    """Project combining all mixins (Level 6 from BaseEntity)."""

    def __init__(self, project_id: str, name: str, created_by: str):
        """Initialize project."""
        super().__init__(project_id, name, created_by)
        self.description = ""
        self.documents: list[Document] = []
        self.tasks: list[Task] = []
        self.tags = []
        self.subscribers = []

    def add_document(self, doc: Document) -> None:
        """Add document to project."""
        self.documents.append(doc)
        self.notify(f"Document added: {doc.name}")

    def add_task(self, task: Task) -> None:
        """Add task to project."""
        self.tasks.append(task)
        self.notify(f"Task added: {task.name}")

    def get_completion_rate(self) -> float:
        """Get task completion rate."""
        if not self.tasks:
            return 1.0
        completed = sum(1 for t in self.tasks if t.status == "completed")
        return completed / len(self.tasks)

    def validate(self) -> bool:
        """Validate project."""
        return super().validate()


# ============================================================================
# Diamond Inheritance Example
# ============================================================================


class DiamondBase:
    """Base class for diamond inheritance."""

    def __init__(self, value: int):
        """Initialize base."""
        self.value = value

    def get_value(self) -> int:
        """Get value."""
        return self.value


class DiamondLeft(DiamondBase):
    """Left branch of diamond."""

    def __init__(self, value: int, left_extra: str):
        """Initialize left branch."""
        super().__init__(value)
        self.left_extra = left_extra

    def get_left(self) -> str:
        """Get left extra."""
        return self.left_extra


class DiamondRight(DiamondBase):
    """Right branch of diamond."""

    def __init__(self, value: int, right_extra: str):
        """Initialize right branch."""
        super().__init__(value)
        self.right_extra = right_extra

    def get_right(self) -> str:
        """Get right extra."""
        return self.right_extra


class DiamondBottom(DiamondLeft, DiamondRight):
    """Bottom of diamond (multiple inheritance)."""

    def __init__(self, value: int, left_extra: str, right_extra: str, bottom_extra: str):
        """Initialize bottom."""
        DiamondLeft.__init__(self, value, left_extra)
        DiamondRight.__init__(self, value, right_extra)
        self.bottom_extra = bottom_extra

    def get_all(self) -> dict[str, Any]:
        """Get all values."""
        return {
            "value": self.get_value(),
            "left": self.get_left(),
            "right": self.get_right(),
            "bottom": self.bottom_extra,
        }
