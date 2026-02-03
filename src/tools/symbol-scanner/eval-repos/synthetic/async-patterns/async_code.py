"""Async/await patterns test repo."""

import asyncio
from typing import AsyncGenerator, AsyncIterator, Callable, Any


# ============================================================================
# Basic Async Functions
# ============================================================================


async def simple_async() -> str:
    """Simple async function."""
    await asyncio.sleep(0.1)
    return "done"


async def async_with_params(url: str, timeout: float = 30.0) -> dict:
    """Async function with parameters."""
    await asyncio.sleep(0.01)
    return {"url": url, "status": 200}


async def fetch_data(url: str) -> bytes:
    """Fetch data from URL."""
    await asyncio.sleep(0.01)
    return b"response data"


async def process_items(items: list[str]) -> list[str]:
    """Process items asynchronously."""
    results = []
    for item in items:
        await asyncio.sleep(0.001)
        results.append(item.upper())
    return results


# ============================================================================
# Async Generators
# ============================================================================


async def async_range(n: int) -> AsyncGenerator[int, None]:
    """Async generator yielding numbers."""
    for i in range(n):
        await asyncio.sleep(0.001)
        yield i


async def async_file_lines(filepath: str) -> AsyncGenerator[str, None]:
    """Async generator for file lines."""
    lines = ["line 1", "line 2", "line 3"]
    for line in lines:
        await asyncio.sleep(0.001)
        yield line


async def paginated_fetch(total: int, page_size: int = 10) -> AsyncGenerator[list[int], None]:
    """Async generator for paginated data."""
    for offset in range(0, total, page_size):
        await asyncio.sleep(0.01)
        page = list(range(offset, min(offset + page_size, total)))
        yield page


# ============================================================================
# Async Context Managers
# ============================================================================


class AsyncResource:
    """Async resource with context manager."""

    def __init__(self, name: str):
        """Initialize resource."""
        self.name = name
        self.is_open = False

    async def __aenter__(self) -> "AsyncResource":
        """Enter async context."""
        await asyncio.sleep(0.01)
        self.is_open = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        await asyncio.sleep(0.01)
        self.is_open = False

    async def read(self) -> str:
        """Read from resource."""
        if not self.is_open:
            raise RuntimeError("Resource not open")
        return f"data from {self.name}"


class AsyncConnection:
    """Async database connection."""

    def __init__(self, dsn: str):
        """Initialize connection."""
        self.dsn = dsn
        self.connected = False
        self.transaction_active = False

    async def connect(self) -> None:
        """Connect to database."""
        await asyncio.sleep(0.01)
        self.connected = True

    async def disconnect(self) -> None:
        """Disconnect from database."""
        await asyncio.sleep(0.01)
        self.connected = False

    async def execute(self, query: str) -> list[dict]:
        """Execute query."""
        if not self.connected:
            raise RuntimeError("Not connected")
        await asyncio.sleep(0.01)
        return [{"result": "data"}]

    async def begin_transaction(self) -> None:
        """Begin transaction."""
        self.transaction_active = True

    async def commit(self) -> None:
        """Commit transaction."""
        self.transaction_active = False

    async def rollback(self) -> None:
        """Rollback transaction."""
        self.transaction_active = False


# ============================================================================
# Async Iterators
# ============================================================================


class AsyncCounter(AsyncIterator[int]):
    """Async iterator that counts."""

    def __init__(self, limit: int):
        """Initialize counter."""
        self.limit = limit
        self.current = 0

    def __aiter__(self) -> "AsyncCounter":
        """Return async iterator."""
        return self

    async def __anext__(self) -> int:
        """Get next value."""
        if self.current >= self.limit:
            raise StopAsyncIteration
        await asyncio.sleep(0.001)
        value = self.current
        self.current += 1
        return value


# ============================================================================
# Concurrent Patterns
# ============================================================================


async def gather_results(urls: list[str]) -> list[dict]:
    """Gather results from multiple URLs concurrently."""
    tasks = [async_with_params(url) for url in urls]
    return await asyncio.gather(*tasks)


async def run_with_timeout(coro: Any, timeout: float) -> Any:
    """Run coroutine with timeout."""
    return await asyncio.wait_for(coro, timeout=timeout)


async def run_first_completed(tasks: list[Any]) -> Any:
    """Return first completed task result."""
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    return done.pop().result()


async def producer_consumer() -> list[str]:
    """Producer-consumer pattern with queue."""
    queue: asyncio.Queue[str] = asyncio.Queue()
    results: list[str] = []

    async def producer() -> None:
        """Produce items."""
        for i in range(5):
            await queue.put(f"item_{i}")
            await asyncio.sleep(0.01)
        await queue.put(None)

    async def consumer() -> None:
        """Consume items."""
        while True:
            item = await queue.get()
            if item is None:
                break
            results.append(item)
            queue.task_done()

    await asyncio.gather(producer(), consumer())
    return results


# ============================================================================
# Async Callbacks and Event Handling
# ============================================================================


class AsyncEventEmitter:
    """Async event emitter."""

    def __init__(self) -> None:
        """Initialize emitter."""
        self._handlers: dict[str, list[Callable]] = {}

    def on(self, event: str, handler: Callable) -> None:
        """Register event handler."""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    async def emit(self, event: str, *args: Any) -> None:
        """Emit event to all handlers."""
        if event in self._handlers:
            for handler in self._handlers[event]:
                if asyncio.iscoroutinefunction(handler):
                    await handler(*args)
                else:
                    handler(*args)


async def retry_async(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
) -> Any:
    """Retry async function on failure."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
    raise last_error


async def debounce_async(
    func: Callable,
    delay: float,
) -> Callable:
    """Create debounced async function."""
    task: asyncio.Task | None = None

    async def debounced(*args: Any) -> Any:
        nonlocal task
        if task:
            task.cancel()
        task = asyncio.create_task(asyncio.sleep(delay))
        try:
            await task
            return await func(*args)
        except asyncio.CancelledError:
            pass

    return debounced
