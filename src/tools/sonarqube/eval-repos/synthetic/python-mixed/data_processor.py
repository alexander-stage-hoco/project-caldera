"""
Data processor module with intentional code quality issues.
Contains complexity, code smells, and some security issues for SonarQube testing.
"""

import os
import json
import sqlite3
from typing import Any, Dict, List, Optional


# Code smell: Too many global variables
GLOBAL_CONFIG = {}
GLOBAL_CACHE = {}
GLOBAL_COUNTER = 0
DEBUG_MODE = True


class DataProcessor:
    """Data processor with intentional code quality issues."""

    def __init__(self):
        # Bug: Mutable default argument would be an issue if in signature
        self.cache = {}
        self.processed_count = 0

    # Code smell: Function too complex (high cyclomatic complexity)
    def process_data(self, data: Dict[str, Any], mode: str, flags: List[str]) -> Dict:
        """Process data with too many branches."""
        result = {}

        if mode == "fast":
            if "priority" in flags:
                if data.get("type") == "A":
                    result["processed"] = True
                    result["mode"] = "fast-priority-A"
                elif data.get("type") == "B":
                    result["processed"] = True
                    result["mode"] = "fast-priority-B"
                else:
                    result["processed"] = False
                    result["mode"] = "fast-priority-unknown"
            else:
                if data.get("type") == "A":
                    result["processed"] = True
                    result["mode"] = "fast-normal-A"
                else:
                    result["processed"] = True
                    result["mode"] = "fast-normal-other"
        elif mode == "slow":
            if "thorough" in flags:
                if data.get("size", 0) > 1000:
                    result["processed"] = True
                    result["mode"] = "slow-thorough-large"
                else:
                    result["processed"] = True
                    result["mode"] = "slow-thorough-small"
            else:
                result["processed"] = True
                result["mode"] = "slow-basic"
        elif mode == "batch":
            if "parallel" in flags:
                result["processed"] = True
                result["mode"] = "batch-parallel"
            elif "sequential" in flags:
                result["processed"] = True
                result["mode"] = "batch-sequential"
            else:
                result["processed"] = True
                result["mode"] = "batch-default"
        else:
            result["processed"] = False
            result["error"] = "Unknown mode"

        return result

    # Code smell: Duplicate code pattern
    def validate_user_data(self, user: Dict) -> List[str]:
        """Validate user data with duplicated validation logic."""
        errors = []

        if not user.get("name"):
            errors.append("Name is required")
        if len(user.get("name", "")) < 2:
            errors.append("Name must be at least 2 characters")
        if len(user.get("name", "")) > 100:
            errors.append("Name must be at most 100 characters")

        if not user.get("email"):
            errors.append("Email is required")
        if len(user.get("email", "")) < 5:
            errors.append("Email must be at least 5 characters")
        if len(user.get("email", "")) > 200:
            errors.append("Email must be at most 200 characters")

        if not user.get("phone"):
            errors.append("Phone is required")
        if len(user.get("phone", "")) < 10:
            errors.append("Phone must be at least 10 characters")
        if len(user.get("phone", "")) > 20:
            errors.append("Phone must be at most 20 characters")

        return errors

    # Code smell: Duplicate code - same pattern as above
    def validate_product_data(self, product: Dict) -> List[str]:
        """Validate product data with duplicated validation logic."""
        errors = []

        if not product.get("name"):
            errors.append("Name is required")
        if len(product.get("name", "")) < 2:
            errors.append("Name must be at least 2 characters")
        if len(product.get("name", "")) > 100:
            errors.append("Name must be at most 100 characters")

        if not product.get("description"):
            errors.append("Description is required")
        if len(product.get("description", "")) < 10:
            errors.append("Description must be at least 10 characters")
        if len(product.get("description", "")) > 1000:
            errors.append("Description must be at most 1000 characters")

        if not product.get("sku"):
            errors.append("SKU is required")
        if len(product.get("sku", "")) < 5:
            errors.append("SKU must be at least 5 characters")
        if len(product.get("sku", "")) > 50:
            errors.append("SKU must be at most 50 characters")

        return errors

    # Bug: SQL injection vulnerability
    def find_by_name(self, name: str) -> List[Dict]:
        """Find records by name - VULNERABLE to SQL injection."""
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        # VULNERABILITY: SQL injection
        query = f"SELECT * FROM records WHERE name = '{name}'"
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results

    # Code smell: Too many parameters
    def create_report(
        self,
        title: str,
        subtitle: str,
        author: str,
        date: str,
        department: str,
        category: str,
        priority: str,
        status: str,
        tags: List[str],
        metadata: Dict,
    ) -> Dict:
        """Create report with too many parameters."""
        return {
            "title": title,
            "subtitle": subtitle,
            "author": author,
            "date": date,
            "department": department,
            "category": category,
            "priority": priority,
            "status": status,
            "tags": tags,
            "metadata": metadata,
        }

    # Code smell: Empty except block (bug)
    def safe_parse(self, data: str) -> Optional[Dict]:
        """Parse data with swallowed exception."""
        try:
            return json.loads(data)
        except:  # noqa: E722 - bare except for testing
            pass  # Bug: silently swallowing exception
        return None

    # Code smell: Unused variable
    def calculate_total(self, items: List[Dict]) -> float:
        """Calculate total with unused variable."""
        unused_variable = "this is never used"  # Code smell
        debug_info = []  # Another unused variable

        total = 0.0
        for item in items:
            total += item.get("price", 0) * item.get("quantity", 0)
        return total
