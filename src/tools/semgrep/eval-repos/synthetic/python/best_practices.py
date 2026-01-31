"""
Test file for BEST_PRACTICE_VIOLATION detection.
Tests deprecated APIs, bare except, eval(), magic numbers.
"""

import os
import subprocess
import pickle


# 1. Using os.popen (deprecated)
def run_command_popen(cmd):
    """BEST_PRACTICE: os.popen is deprecated, use subprocess instead."""
    result = os.popen(cmd)
    return result.read()


# 2. Bare except clause
def risky_operation(data):
    """BEST_PRACTICE: Bare except catches everything including SystemExit."""
    try:
        process(data)
    except:  # Bare except - catches all exceptions
        pass


# 3. Using eval with user input
def evaluate_expression(expr):
    """BEST_PRACTICE: eval() is dangerous with untrusted input."""
    result = eval(expr)  # Security and maintainability risk
    return result


# 4. Using exec with user input
def execute_code(code):
    """BEST_PRACTICE: exec() is dangerous with untrusted input."""
    exec(code)  # Security and maintainability risk


# 5. Magic numbers
def calculate_discount(price):
    """BEST_PRACTICE: Magic numbers should be named constants."""
    if price > 100:
        return price * 0.15  # Magic number - what does 0.15 mean?
    return price * 0.05  # Another magic number


# 6. Using pickle.loads on untrusted data
def deserialize_data(data):
    """BEST_PRACTICE: pickle.loads is dangerous with untrusted data."""
    return pickle.loads(data)


# GOOD: Correct pattern for subprocess
def run_command_correct(cmd):
    """Good: Use subprocess.run instead of os.popen."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout


# GOOD: Specific exception handling
def safe_operation(data):
    """Good: Catch specific exceptions."""
    try:
        process(data)
    except ValueError as e:
        handle_error(e)
    except KeyError as e:
        handle_error(e)


# GOOD: Named constants
STANDARD_DISCOUNT = 0.05
PREMIUM_DISCOUNT = 0.15
PREMIUM_THRESHOLD = 100

def calculate_discount_correct(price):
    """Good: Use named constants instead of magic numbers."""
    if price > PREMIUM_THRESHOLD:
        return price * PREMIUM_DISCOUNT
    return price * STANDARD_DISCOUNT


def process(data):
    """Stub function."""
    pass


def handle_error(e):
    """Stub function."""
    pass
