"""Dynamic code generation patterns that challenge static analysis."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING


def create_function_with_exec():
    """Create a function dynamically using exec()."""
    code = """
def dynamic_greet(name):
    return f"Hello, {name}!"
"""
    local_vars = {}
    exec(code, {}, local_vars)
    return local_vars["dynamic_greet"]


def compute_with_eval(expression: str) -> int:
    """Evaluate a mathematical expression using eval()."""
    allowed = {
        "abs": abs,
        "min": min,
        "max": max,
    }
    return eval(expression, {"__builtins__": {}}, allowed)


class DynamicLoader:
    """Class that dynamically imports modules."""

    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None

    def get_module(self):
        """Lazily load the module."""
        if self._module is None:
            self._module = importlib.import_module(self.module_name)
        return self._module

    def call_function(self, func_name: str, *args):
        """Call a function from the dynamically loaded module."""
        module = self.get_module()
        func = getattr(module, func_name)
        return func(*args)


def _private_helper():
    """Private helper function (should have reduced weight)."""
    return "private"


def generate_class_dynamically(class_name: str):
    """Generate a class dynamically using type()."""
    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

    return type(class_name, (), {
        "__init__": __init__,
        "get_value": get_value,
    })


if __name__ == "__main__":
    # Test dynamic function creation
    greet = create_function_with_exec()
    print(greet("World"))

    # Test eval
    result = compute_with_eval("min(10, 20)")
    print(f"Eval result: {result}")

    # Test dynamic class
    MyClass = generate_class_dynamically("MyClass")
    obj = MyClass(42)
    print(f"Dynamic object value: {obj.get_value()}")
