"""
Test file for DD smell D1_EMPTY_CATCH detection.
Contains multiple empty catch blocks.
"""

import json


def process_user_data(user_id: int) -> dict:
    """Process user data with problematic exception handling."""
    try:
        # Fetch user from database
        user = fetch_user(user_id)
        return user
    except Exception:
        # D1_EMPTY_CATCH: Empty catch block - swallows all errors silently
        pass


def load_config(path: str) -> dict:
    """Load configuration from file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # D1_EMPTY_CATCH: Another empty catch
        pass
    except json.JSONDecodeError:
        # D1_EMPTY_CATCH: Yet another empty catch
        pass
    return {}


def dangerous_operation(data: list) -> None:
    """Perform operations that might fail."""
    for item in data:
        try:
            process_item(item)
        except ValueError:
            # D1_EMPTY_CATCH: Empty catch in loop
            pass
        except KeyError:
            # D1_EMPTY_CATCH: Multiple empty catches
            pass


def fetch_user(user_id: int) -> dict:
    """Stub function."""
    return {"id": user_id, "name": "Test"}


def process_item(item: any) -> None:
    """Stub function."""
    pass


# Another example with bare except
def risky_calculation(x: int, y: int) -> int:
    """Calculate division with poor error handling."""
    try:
        return x // y
    except:
        # D1_EMPTY_CATCH: Bare except with empty body
        pass
    return 0
