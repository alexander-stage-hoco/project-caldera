# -*- coding: utf-8 -*-
"""Confusing names that challenge parsers."""

from __future__ import annotations


# Names that look like Python keywords
def def_(x):
    """Function named 'def_' (keyword with underscore)."""
    return x


def class_(x):
    """Function named 'class_' (keyword with underscore)."""
    return x


def import_(module):
    """Function named 'import_' (keyword with underscore)."""
    return module


def return_(value):
    """Function named 'return_' (keyword with underscore)."""
    return value


# Dunder-like names (but not actual dunders)
def __custom__(x):
    """Function with dunder-style name."""
    return x


def ___triple_underscore(x):
    """Function with triple underscore prefix."""
    return x


# Unicode identifiers
def calculate_area(length, width):
    """Unicode variable names inside."""
    return length * width


class Data:
    """Class using unicode internally."""

    def __init__(self, value):
        self.value = value

    def process(self):
        """Method with unicode variable."""
        result = self.value * 2
        return result


# Single character names
def a(x):
    """Single character function name."""
    return x


def _(x):
    """Underscore-only function name."""
    return x


def __(x):
    """Double underscore function name."""
    return x


# Numbers in names
def func123(x):
    """Function with numbers."""
    return x


def _123private(x):
    """Private function starting with underscore then number."""
    return x


class Class2(Data):
    """Class with number in name."""

    def method_1(self):
        """Method with number."""
        return 1

    def method_2(self):
        """Another method with number."""
        return 2


# Names with repeated patterns
def processprocess(x):
    """Repeated word in name."""
    return x


def ALLCAPS(x):
    """All caps function name (usually constants)."""
    return x


# Edge case: name collision with builtins
def list(items):  # noqa: A001
    """Function shadowing builtin 'list'."""
    return items


def dict(mapping):  # noqa: A001
    """Function shadowing builtin 'dict'."""
    return mapping


# Private variations
def _single_underscore():
    """Single underscore prefix."""
    return 1


def __double_underscore():
    """Double underscore prefix (but not a method)."""
    return 2


class _PrivateClass:
    """Private class with underscore prefix."""

    def public_method(self):
        """Public method in private class."""
        return "public"

    def _private_method(self):
        """Private method in private class."""
        return "private"


if __name__ == "__main__":
    # Use the confusing functions
    print(def_(1))
    print(class_(2))
    print(import_("os"))
    print(return_(42))
    print(__custom__(3))
    print(a(4))
    print(_(5))
    print(__(6))
    print(func123(7))
    print(_123private(8))
    print(ALLCAPS(9))
    print(list([1, 2, 3]))
    print(dict({"a": 1}))
