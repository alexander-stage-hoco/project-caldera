"""Base SonarQube API client with pagination and retry support."""

from dataclasses import dataclass, field
from typing import Any, Iterator
import time

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)


@dataclass
class ApiConfig:
    """Configuration for the SonarQube API client."""

    base_url: str = "http://localhost:9000"
    token: str | None = None  # Admin token if required
    page_size: int = 500
    max_retries: int = 3
    timeout: int = 60
    # Metric chunking - SonarQube limits to 15 metrics per request
    metrics_chunk_size: int = 15


@dataclass
class PageInfo:
    """Pagination information from SonarQube API responses."""

    page_index: int
    page_size: int
    total: int

    @property
    def has_more(self) -> bool:
        """Check if there are more pages."""
        return self.page_index * self.page_size < self.total

    @classmethod
    def from_response(cls, data: dict) -> "PageInfo":
        """Create PageInfo from API response paging data."""
        paging = data.get("paging", {})
        return cls(
            page_index=paging.get("pageIndex", 1),
            page_size=paging.get("pageSize", 100),
            total=paging.get("total", 0),
        )


class SonarQubeApiError(Exception):
    """Raised when SonarQube API returns an error."""

    def __init__(self, message: str, status_code: int | None = None, errors: list | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or []


class SonarQubeClient:
    """HTTP client for SonarQube REST API with pagination and retry support."""

    def __init__(self, config: ApiConfig | None = None):
        """Initialize the client.

        Args:
            config: API configuration. Uses defaults if None.
        """
        self.config = config or ApiConfig()
        self._client: httpx.Client | None = None
        self.api_calls: list[dict] = []

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            headers = {}
            auth = None
            if self.config.token:
                # SonarQube uses token as username with empty password
                auth = httpx.BasicAuth(self.config.token, "")

            self._client = httpx.Client(
                base_url=self.config.base_url,
                headers=headers,
                auth=auth,
                timeout=self.config.timeout,
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "SonarQubeClient":
        """Support context manager usage."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close client on context exit."""
        self.close()

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json: JSON body for POST requests

        Returns:
            Parsed JSON response

        Raises:
            SonarQubeApiError: If the API returns an error
        """
        logger.debug("API request", method=method, endpoint=endpoint, params=params)

        start = time.perf_counter()
        response = self.client.request(
            method=method,
            url=endpoint,
            params=params,
            json=json,
        )
        duration_ms = (time.perf_counter() - start) * 1000
        self.api_calls.append(
            {
                "method": method,
                "endpoint": endpoint,
                "duration_ms": round(duration_ms, 2),
                "status_code": response.status_code,
            }
        )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                errors = error_data.get("errors", [])
                msg = "; ".join(e.get("msg", str(e)) for e in errors) or response.text
            except Exception:
                msg = response.text

            raise SonarQubeApiError(
                f"API error: {msg}",
                status_code=response.status_code,
                errors=errors if "errors" in dir() else [],
            )

        if not response.text:
            return {}

        return response.json()

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, params: dict | None = None, json: dict | None = None) -> dict:
        """Make a POST request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            json: JSON body

        Returns:
            Parsed JSON response
        """
        return self._request("POST", endpoint, params=params, json=json)

    def get_system_status(self) -> dict:
        """Fetch SonarQube system status metadata."""
        return self._request("GET", "/api/system/status")

    def get_paged(
        self,
        endpoint: str,
        params: dict | None = None,
        items_key: str = "components",
        page_size: int | None = None,
    ) -> Iterator[dict]:
        """Make paginated GET requests, yielding all items.

        Automatically handles pagination by following page indices until
        all items have been retrieved.

        Args:
            endpoint: API endpoint path
            params: Base query parameters (p and ps will be added)
            items_key: Key in response containing the list of items
            page_size: Items per page (uses config default if None)

        Yields:
            Individual items from all pages
        """
        params = dict(params) if params else {}
        page_size = page_size or self.config.page_size
        page = 1

        while True:
            params["p"] = page
            params["ps"] = page_size

            logger.debug("Fetching page", endpoint=endpoint, page=page, page_size=page_size)
            data = self.get(endpoint, params)

            items = data.get(items_key, [])
            for item in items:
                yield item

            page_info = PageInfo.from_response(data)
            if not page_info.has_more:
                logger.debug(
                    "Pagination complete",
                    endpoint=endpoint,
                    total_items=page_info.total,
                    pages=page,
                )
                break

            page += 1

    def get_all(
        self,
        endpoint: str,
        params: dict | None = None,
        items_key: str = "components",
        page_size: int | None = None,
    ) -> list[dict]:
        """Get all items from a paginated endpoint.

        Args:
            endpoint: API endpoint path
            params: Base query parameters
            items_key: Key in response containing the list of items
            page_size: Items per page

        Returns:
            List of all items from all pages
        """
        return list(self.get_paged(endpoint, params, items_key, page_size))

    def get_chunked_metrics(
        self,
        endpoint: str,
        base_params: dict,
        all_metrics: list[str],
        items_key: str = "components",
    ) -> dict[str, dict]:
        """Fetch measures with metrics chunked to avoid API limits.

        SonarQube limits the number of metrics per request (typically 15).
        This method chunks the metric list and merges results.

        Args:
            endpoint: API endpoint path
            base_params: Base query parameters
            all_metrics: Complete list of metrics to fetch
            items_key: Key in response containing component data

        Returns:
            Dictionary mapping component keys to their measures
        """
        chunk_size = self.config.metrics_chunk_size
        results: dict[str, dict] = {}

        for i in range(0, len(all_metrics), chunk_size):
            chunk = all_metrics[i : i + chunk_size]
            params = dict(base_params)
            params["metricKeys"] = ",".join(chunk)

            logger.debug(
                "Fetching metric chunk",
                chunk_index=i // chunk_size,
                metrics=chunk,
            )

            for component in self.get_paged(endpoint, params, items_key):
                key = component.get("key", "")
                if key not in results:
                    results[key] = {"key": key, "measures": []}
                results[key]["measures"].extend(component.get("measures", []))

        return results


@dataclass
class RateLimiter:
    """Simple rate limiter for API requests."""

    requests_per_second: float = 10.0
    _last_request_time: float = field(default=0.0, init=False)

    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        import time

        min_interval = 1.0 / self.requests_per_second
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()
