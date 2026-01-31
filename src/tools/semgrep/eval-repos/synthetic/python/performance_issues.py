"""
Test file for PERFORMANCE_ISSUE detection.
Tests string concat in loop, list += in loop, regex in loop.
"""

import re
from typing import List


# 1. String concatenation in loop
def build_string_inefficient(items):
    """PERFORMANCE: String concat in loop creates many intermediate strings."""
    result = ""
    for item in items:
        result += str(item) + ","  # O(n^2) performance
    return result


# 2. List extend with += in loop (less efficient)
def extend_list_inefficient(lists):
    """PERFORMANCE: Using += to extend list in loop is inefficient."""
    result = []
    for lst in lists:
        result += lst  # Creates new list each iteration
    return result


# 3. Regex compilation in loop
def search_patterns_inefficient(texts, pattern):
    """PERFORMANCE: Compiling regex in loop is wasteful."""
    matches = []
    for text in texts:
        if re.search(pattern, text):  # Regex compiled each iteration
            matches.append(text)
    return matches


# 4. List comprehension with repeated function call
def process_items_inefficient(items):
    """PERFORMANCE: Repeated len() calls in loop condition."""
    i = 0
    while i < len(items):  # len() called each iteration
        process(items[i])
        i += 1


# 5. Using + for list concatenation in loop
def merge_lists_inefficient(lists):
    """PERFORMANCE: List + in loop creates many intermediate lists."""
    result = []
    for lst in lists:
        result = result + lst  # O(n^2) performance
    return result


# GOOD: Correct string building
def build_string_correct(items):
    """Good: Use join() for string building."""
    return ",".join(str(item) for item in items)


# GOOD: Correct list extension
def extend_list_correct(lists):
    """Good: Use list.extend() or itertools.chain."""
    result = []
    for lst in lists:
        result.extend(lst)
    return result


# GOOD: Pre-compiled regex
PATTERN = re.compile(r'\d+')

def search_patterns_correct(texts):
    """Good: Compile regex once, use many times."""
    matches = []
    for text in texts:
        if PATTERN.search(text):
            matches.append(text)
    return matches


# GOOD: Cache length outside loop
def process_items_correct(items):
    """Good: Cache len() result outside loop."""
    length = len(items)
    i = 0
    while i < length:
        process(items[i])
        i += 1


def process(item):
    """Stub function."""
    pass
