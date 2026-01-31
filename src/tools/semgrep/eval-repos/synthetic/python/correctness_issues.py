"""
Test file for CORRECTNESS_ISSUE detection.
Tests logic errors, mutable defaults, self-comparison, null checks.
"""

from typing import Optional


# 1. Mutable default argument - list
def append_to_list(item, items=[]):
    """CORRECTNESS: Mutable default argument - list will be shared across calls."""
    items.append(item)
    return items


# 2. Mutable default argument - dict
def add_to_cache(key, value, cache={}):
    """CORRECTNESS: Mutable default argument - dict will be shared across calls."""
    cache[key] = value
    return cache


# 3. Self-comparison (always true/false)
def check_value(x):
    """CORRECTNESS: Comparing value to itself is always True."""
    if x == x:  # Self-comparison
        return True
    return False


# 4. Using is instead of == for value comparison
def check_string_match(s):
    """CORRECTNESS: Using 'is' with string literal can fail."""
    if s is "hello":  # Should use == for value comparison
        return True
    return False


# 5. None comparison with == instead of is
def check_none(value):
    """CORRECTNESS: Should use 'is None' instead of '== None'."""
    if value == None:  # Should use 'is None'
        return "null"
    return "not null"


# GOOD: Correct pattern for mutable default
def append_to_list_correct(item, items=None):
    """Good: Initialize mutable default in function body."""
    if items is None:
        items = []
    items.append(item)
    return items


# GOOD: Correct self-comparison pattern
def check_nan(x):
    """Good: Self-comparison is valid for NaN check."""
    import math
    return math.isnan(x)


# GOOD: Correct None comparison
def check_none_correct(value):
    """Good: Use 'is None' for None checks."""
    if value is None:
        return "null"
    return "not null"


# 6. Integer comparison with 'is'
def check_large_int(x):
    """CORRECTNESS: Using 'is' with integers outside cache range."""
    if x is 1000:  # Large integers may not be cached
        return True
    return False
