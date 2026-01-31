"""
API handler module with security vulnerabilities and code smells.
For SonarQube testing of Python analysis capabilities.
"""

import os
import hashlib
import pickle
import subprocess
from typing import Any, Dict, Optional


# Security: Hardcoded credentials
API_KEY = "sk-prod-1234567890abcdef"
DB_PASSWORD = "admin123"
SECRET_TOKEN = "super_secret_token_12345"


class ApiHandler:
    """API handler with intentional security issues."""

    def __init__(self):
        # Security: Hardcoded connection string
        self.db_url = "postgresql://admin:password123@localhost:5432/production"
        self.debug = True

    # Security: Command injection vulnerability
    def run_diagnostic(self, host: str) -> str:
        """Run diagnostic command - VULNERABLE to command injection."""
        # VULNERABILITY: User input directly in shell command
        command = f"ping -c 4 {host}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout

    # Security: Insecure deserialization
    def load_session(self, session_data: bytes) -> Any:
        """Load session data - VULNERABLE to insecure deserialization."""
        # VULNERABILITY: Deserializing untrusted data
        return pickle.loads(session_data)

    # Security: Weak hash algorithm
    def hash_password(self, password: str) -> str:
        """Hash password - using weak algorithm."""
        # VULNERABILITY: MD5 is cryptographically weak
        return hashlib.md5(password.encode()).hexdigest()

    # Security: Path traversal
    def read_config(self, config_name: str) -> str:
        """Read config file - VULNERABLE to path traversal."""
        # VULNERABILITY: No path validation
        config_path = f"/app/configs/{config_name}"
        with open(config_path, "r") as f:
            return f.read()

    # Code smell: Function does too many things
    def process_request(
        self, request: Dict, user: Dict, settings: Dict
    ) -> Dict[str, Any]:
        """Process request - does too many unrelated things."""
        result = {"success": False}

        # Validate user
        if not user.get("id"):
            result["error"] = "Invalid user"
            return result
        if not user.get("active"):
            result["error"] = "User inactive"
            return result

        # Parse request
        action = request.get("action")
        if not action:
            result["error"] = "No action specified"
            return result

        # Check permissions
        allowed_actions = settings.get("allowed_actions", [])
        if action not in allowed_actions:
            result["error"] = "Action not allowed"
            return result

        # Log request
        if settings.get("logging_enabled"):
            self._log_request(request, user)

        # Execute action
        if action == "create":
            result["data"] = self._create_item(request.get("data", {}))
        elif action == "update":
            result["data"] = self._update_item(
                request.get("id"), request.get("data", {})
            )
        elif action == "delete":
            result["data"] = self._delete_item(request.get("id"))
        elif action == "list":
            result["data"] = self._list_items(request.get("filters", {}))
        else:
            result["error"] = "Unknown action"
            return result

        result["success"] = True
        return result

    def _log_request(self, request: Dict, user: Dict) -> None:
        """Log request - stub."""
        pass

    def _create_item(self, data: Dict) -> Dict:
        """Create item - stub."""
        return {"id": 1, **data}

    def _update_item(self, item_id: int, data: Dict) -> Dict:
        """Update item - stub."""
        return {"id": item_id, **data}

    def _delete_item(self, item_id: int) -> bool:
        """Delete item - stub."""
        return True

    def _list_items(self, filters: Dict) -> list:
        """List items - stub."""
        return []

    # Code smell: Dead code
    def deprecated_method(self) -> None:
        """This method is never called - dead code."""
        print("This code is never executed")
        x = 1 + 2
        y = x * 3
        return None

    # Bug: Infinite loop potential
    def wait_for_response(self, timeout: int) -> Optional[Dict]:
        """Wait for response - potential infinite loop."""
        elapsed = 0
        response = None

        # Bug: If timeout is negative, this could be problematic
        while elapsed < timeout:
            response = self._check_response()
            if response:
                return response
            # Missing increment of elapsed - infinite loop
            # elapsed += 1  # This line is intentionally missing

        return response

    def _check_response(self) -> Optional[Dict]:
        """Check for response - stub."""
        return None

    # Code smell: Too deeply nested
    def complex_validation(self, data: Dict) -> bool:
        """Complex validation with deep nesting."""
        if data:
            if "user" in data:
                if data["user"].get("verified"):
                    if "permissions" in data["user"]:
                        if "admin" in data["user"]["permissions"]:
                            if data.get("action") == "delete":
                                if data.get("target"):
                                    if data["target"].get("deletable"):
                                        return True
        return False
