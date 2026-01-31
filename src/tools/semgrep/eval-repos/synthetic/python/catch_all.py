"""
Test file for DD smell D2_CATCH_ALL detection.
Contains broad exception catching without specific handling.
"""

import logging

logger = logging.getLogger(__name__)


def handle_request(request_data: dict) -> dict:
    """Handle incoming request with overly broad exception catching."""
    try:
        # Parse and validate request
        validated = validate_request(request_data)
        result = process_validated_data(validated)
        return {"status": "success", "data": result}
    except Exception as e:
        # D2_CATCH_ALL: Catching base Exception without specific handling
        logger.error(f"Request failed: {e}")
        return {"status": "error", "message": "Request failed"}


def fetch_and_process(url: str) -> str:
    """Fetch data from URL and process it."""
    try:
        response = make_http_request(url)
        data = parse_response(response)
        return transform_data(data)
    except BaseException as e:
        # D2_CATCH_ALL: Catching BaseException is even worse
        return f"Error: {e}"


def batch_process(items: list) -> list:
    """Process multiple items with poor error handling."""
    results = []
    for item in items:
        try:
            processed = transform_item(item)
            results.append(processed)
        except Exception:
            # D2_CATCH_ALL: Generic exception catching in loop
            results.append(None)
    return results


def dangerous_io_operation(path: str) -> bytes:
    """Perform IO operation with overly broad catching."""
    try:
        with open(path, 'rb') as f:
            return f.read()
    except:
        # D2_CATCH_ALL: Bare except is even broader
        return b""


# Stub functions
def validate_request(data: dict) -> dict:
    return data


def process_validated_data(data: dict) -> dict:
    return data


def make_http_request(url: str) -> bytes:
    return b""


def parse_response(response: bytes) -> dict:
    return {}


def transform_data(data: dict) -> str:
    return ""


def transform_item(item: any) -> any:
    return item
