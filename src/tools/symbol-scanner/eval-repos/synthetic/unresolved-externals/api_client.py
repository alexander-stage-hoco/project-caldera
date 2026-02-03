"""API client with stdlib and third-party calls."""

import json
import urllib.request
from datetime import datetime
from typing import Any


def fetch_data(url: str) -> dict[str, Any]:
    """Fetch JSON data from URL."""
    with urllib.request.urlopen(url) as response:
        data = response.read()
        return json.loads(data)


def get_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now().isoformat()


def parse_json(text: str) -> dict:
    """Parse JSON string."""
    return json.loads(text)


def serialize(data: dict) -> str:
    """Serialize dict to JSON."""
    return json.dumps(data, indent=2)


class ApiClient:
    """Simple API client."""

    def __init__(self, base_url: str):
        """Initialize client."""
        self.base_url = base_url
        self.created_at = get_timestamp()

    def get(self, endpoint: str) -> dict:
        """GET request to endpoint."""
        url = f"{self.base_url}/{endpoint}"
        return fetch_data(url)

    def process_response(self, response: dict) -> str:
        """Process API response."""
        return serialize(response)
