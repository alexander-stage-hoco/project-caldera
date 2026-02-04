"""Pytest fixtures for symbol-scanner tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def simple_function_code():
    """Simple Python code with functions."""
    return '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def main():
    print(hello("World"))
    result = add(1, 2)
    print(result)
'''


@pytest.fixture
def class_code():
    """Python code with classes and methods."""
    return '''
class Calculator:
    """A simple calculator class."""

    def __init__(self):
        """Initialize calculator."""
        self.result = 0

    def add(self, x: int, y: int) -> int:
        """Add two numbers."""
        self.result = x + y
        return self.result

    def _internal(self):
        """Internal method."""
        pass


class AdvancedCalculator(Calculator):
    """Advanced calculator with more operations."""

    def multiply(self, x: int, y: int) -> int:
        """Multiply two numbers."""
        self.result = x * y
        return self.result
'''


@pytest.fixture
def import_code():
    """Python code with various import styles."""
    return '''
import os
import sys

from pathlib import Path
from typing import Optional, List

import json as json_lib

from collections import *


def use_imports():
    path = Path(".")
    data = json_lib.loads("{}")
    return os.getcwd()
'''


@pytest.fixture
def cross_module_repo(temp_dir):
    """Create a multi-file test repo."""
    # utils.py
    (temp_dir / "utils.py").write_text('''
def validate(data):
    return bool(data)

def sanitize(text):
    return text.strip()
''')

    # main.py
    (temp_dir / "main.py").write_text('''
from utils import validate, sanitize

def process(data):
    if validate(data):
        return sanitize(data)
    return None
''')

    return temp_dir


# ============ C# Code Fixtures ============


@pytest.fixture
def csharp_class_code():
    """C# code with a class, constructor, methods, and properties."""
    return '''
public class Calculator
{
    private int _value;

    public int Value { get; set; }

    public Calculator(int initial)
    {
        _value = initial;
    }

    public int Add(int x, int y)
    {
        return x + y;
    }

    private int _internalMethod()
    {
        return _value;
    }
}
'''


@pytest.fixture
def csharp_struct_code():
    """C# struct definition."""
    return '''
public struct Point
{
    public int X { get; set; }
    public int Y { get; set; }

    public Point(int x, int y)
    {
        X = x;
        Y = y;
    }

    public double Distance(Point other)
    {
        int dx = X - other.X;
        int dy = Y - other.Y;
        return Math.Sqrt(dx * dx + dy * dy);
    }
}
'''


@pytest.fixture
def csharp_interface_code():
    """C# interface definition."""
    return '''
public interface ICalculator
{
    int Add(int x, int y);
    int Subtract(int x, int y);
    int Value { get; set; }
}
'''


@pytest.fixture
def csharp_record_code():
    """C# record definition (C# 9+)."""
    return '''
public record Person(string FirstName, string LastName)
{
    public string FullName => $"{FirstName} {LastName}";
}
'''


@pytest.fixture
def csharp_enum_code():
    """C# enum definition."""
    return '''
public enum Color
{
    Red,
    Green,
    Blue
}
'''


@pytest.fixture
def csharp_nested_class_code():
    """C# code with nested class."""
    return '''
public class Outer
{
    private class Inner
    {
        public int Value { get; set; }
    }

    public void UseInner()
    {
        var inner = new Inner();
        inner.Value = 42;
    }
}
'''


@pytest.fixture
def csharp_visibility_code():
    """C# code with various visibility modifiers."""
    return '''
public class VisibilityTest
{
    public int PublicField;
    internal int InternalField;
    protected int ProtectedField;
    private int PrivateField;

    public void PublicMethod() { }
    internal void InternalMethod() { }
    protected void ProtectedMethod() { }
    private void PrivateMethod() { }
}
'''


@pytest.fixture
def csharp_static_code():
    """C# code with static members."""
    return '''
public static class MathHelper
{
    public static int Add(int x, int y)
    {
        return x + y;
    }

    public static readonly double PI = 3.14159;
}
'''


@pytest.fixture
def csharp_async_code():
    """C# async method code."""
    return '''
public class AsyncExample
{
    public async Task<string> FetchDataAsync(string url)
    {
        await Task.Delay(100);
        return "data";
    }

    public async Task ProcessAsync()
    {
        var result = await FetchDataAsync("http://example.com");
        Console.WriteLine(result);
    }
}
'''


@pytest.fixture
def csharp_generic_class_code():
    """C# generic class definition."""
    return '''
public class Container<T>
{
    private T _value;

    public Container(T value)
    {
        _value = value;
    }

    public T GetValue()
    {
        return _value;
    }

    public void SetValue(T value)
    {
        _value = value;
    }
}
'''


@pytest.fixture
def csharp_generic_method_code():
    """C# generic method definition."""
    return '''
public class Utilities
{
    public T Identity<T>(T value)
    {
        return value;
    }

    public TResult Convert<TInput, TResult>(TInput input, Func<TInput, TResult> converter)
    {
        return converter(input);
    }
}
'''


@pytest.fixture
def csharp_imports_code():
    """C# code with various using directives."""
    return '''
using System;
using System.Collections.Generic;
using static System.Math;
using Alias = System.Text.StringBuilder;

namespace MyApp
{
    public class ImportExample
    {
        public void UseImports()
        {
            var list = new List<string>();
            var abs = Abs(-5);
            var sb = new Alias();
        }
    }
}
'''


@pytest.fixture
def csharp_global_using_code():
    """C# code with global using (C# 10+)."""
    return '''
global using System;
global using System.Collections.Generic;

namespace MyApp
{
    public class GlobalUsingExample
    {
        public List<string> Items { get; set; }
    }
}
'''


@pytest.fixture
def csharp_calls_code():
    """C# code with various call types."""
    return '''
public class CallExample
{
    public void TestCalls()
    {
        // Direct call
        LocalMethod();

        // Static method call
        var abs = Math.Abs(-5);

        // Instance method call
        var str = "hello";
        var upper = str.ToUpper();

        // Constructor call
        var list = new List<string>();

        // Chained calls
        var result = str.Trim().ToLower().Substring(0, 3);
    }

    private void LocalMethod()
    {
        Console.WriteLine("Local");
    }
}
'''


@pytest.fixture
def csharp_event_code():
    """C# code with events."""
    return '''
public class EventExample
{
    public event EventHandler OnChanged;

    public event EventHandler<string> OnMessage
    {
        add { _handlers += value; }
        remove { _handlers -= value; }
    }

    private EventHandler<string> _handlers;

    public void RaiseChanged()
    {
        OnChanged?.Invoke(this, EventArgs.Empty);
    }
}
'''


@pytest.fixture
def csharp_xml_doc_code():
    """C# code with XML documentation comments."""
    return '''
/// <summary>
/// A calculator class for basic math operations.
/// </summary>
public class DocumentedCalculator
{
    /// <summary>
    /// Adds two integers together.
    /// </summary>
    /// <param name="x">The first number.</param>
    /// <param name="y">The second number.</param>
    /// <returns>The sum of x and y.</returns>
    public int Add(int x, int y)
    {
        return x + y;
    }
}
'''


@pytest.fixture
def csharp_syntax_error_code():
    """C# code with syntax errors for testing error recovery."""
    return '''
public class Broken
{
    public void ValidMethod()
    {
        Console.WriteLine("valid");
    }

    public void BrokenMethod(
    {
        // Missing closing paren
    }

    public void AnotherValidMethod()
    {
        Console.WriteLine("also valid");
    }
}
'''


@pytest.fixture
def csharp_file_scoped_namespace_code():
    """C# code with file-scoped namespace (C# 10+)."""
    return '''
namespace MyApp.Services;

public class ServiceExample
{
    public void DoWork()
    {
        Console.WriteLine("Working");
    }
}
'''


@pytest.fixture
def csharp_cross_file_repo(temp_dir):
    """Create a multi-file C# test repo."""
    # Models.cs
    (temp_dir / "Models.cs").write_text('''
namespace MyApp.Models
{
    public class User
    {
        public int Id { get; set; }
        public string Name { get; set; }
    }
}
''')

    # Services.cs
    (temp_dir / "Services.cs").write_text('''
using MyApp.Models;

namespace MyApp.Services
{
    public class UserService
    {
        public User GetUser(int id)
        {
            return new User { Id = id, Name = "Test" };
        }

        public void SaveUser(User user)
        {
            Console.WriteLine($"Saving {user.Name}");
        }
    }
}
''')

    # Program.cs
    (temp_dir / "Program.cs").write_text('''
using MyApp.Services;

namespace MyApp
{
    public class Program
    {
        public static void Main()
        {
            var service = new UserService();
            var user = service.GetUser(1);
            service.SaveUser(user);
        }
    }
}
''')

    return temp_dir


# ============ Additional C# Language Feature Fixtures ============


@pytest.fixture
def csharp_abstract_class_code():
    """C# abstract class with abstract and virtual methods."""
    return '''
public abstract class Shape
{
    public abstract double Area();
    public virtual string Name => "Shape";
    protected abstract void Draw();
}

public class Circle : Shape
{
    public double Radius { get; set; }
    public override double Area() => Math.PI * Radius * Radius;
    public override string Name => "Circle";
    protected override void Draw() { }
}

public sealed class Square : Shape
{
    public double Side { get; set; }
    public override double Area() => Side * Side;
    protected override void Draw() { }
}
'''


@pytest.fixture
def csharp_local_function_code():
    """C# code with local functions."""
    return '''
public class Calculator
{
    public int Factorial(int n)
    {
        int Calculate(int x)
        {
            return x <= 1 ? 1 : x * Calculate(x - 1);
        }
        return Calculate(n);
    }

    public (int sum, int product) ProcessNumbers(int[] numbers)
    {
        int Sum()
        {
            int total = 0;
            foreach (var n in numbers) total += n;
            return total;
        }

        int Product()
        {
            int result = 1;
            foreach (var n in numbers) result *= n;
            return result;
        }

        return (Sum(), Product());
    }
}
'''


@pytest.fixture
def csharp_linq_query_code():
    """C# code with LINQ query syntax."""
    return '''
using System.Linq;
using System.Collections.Generic;

public class QueryExample
{
    public IEnumerable<int> GetEvens(List<int> numbers)
    {
        var evens = from n in numbers
                    where n % 2 == 0
                    orderby n
                    select n;
        return evens;
    }

    public IEnumerable<string> GetNames(List<Person> people)
    {
        var names = from p in people
                    where p.Age > 18
                    orderby p.LastName, p.FirstName
                    select $"{p.FirstName} {p.LastName}";
        return names;
    }

    public IEnumerable<(string Name, int Count)> GroupByCategory(List<Item> items)
    {
        var grouped = from item in items
                      group item by item.Category into g
                      select (Name: g.Key, Count: g.Count());
        return grouped;
    }
}
'''


@pytest.fixture
def csharp_tuple_code():
    """C# code with tuple return types and deconstruction."""
    return '''
public class TupleExample
{
    public (int, string) GetPair()
    {
        return (42, "answer");
    }

    public (int x, int y, int z) GetCoordinates()
    {
        return (1, 2, 3);
    }

    public void UseTuples()
    {
        var (num, text) = GetPair();
        var (x, y, z) = GetCoordinates();
        (int a, int b) = (10, 20);
    }

    public (T first, T last) GetFirstAndLast<T>(IEnumerable<T> items)
    {
        return (items.First(), items.Last());
    }
}
'''


@pytest.fixture
def csharp_static_constructor_code():
    """C# code with static constructor."""
    return '''
public class Configuration
{
    public static string ConnectionString { get; private set; }
    public static int MaxRetries { get; private set; }

    static Configuration()
    {
        ConnectionString = "default";
        MaxRetries = 3;
    }

    public Configuration() { }

    public void Reset()
    {
        // Instance method
    }
}
'''


@pytest.fixture
def csharp_indexer_code():
    """C# code with indexer declarations."""
    return '''
public class DataCollection
{
    private readonly Dictionary<string, object> _data = new();

    public object this[string key]
    {
        get => _data[key];
        set => _data[key] = value;
    }

    public object this[int index]
    {
        get => _data.Values.ElementAt(index);
    }

    public object this[int x, int y]
    {
        get => _data[$"{x},{y}"];
        set => _data[$"{x},{y}"] = value;
    }
}
'''


@pytest.fixture
def csharp_cross_file_calls_repo(temp_dir):
    """Create a multi-file C# repo specifically for testing cross-file call resolution."""
    # MathUtils.cs
    (temp_dir / "MathUtils.cs").write_text('''
namespace MyApp.Utils
{
    public static class MathUtils
    {
        public static int Add(int a, int b) => a + b;
        public static int Multiply(int a, int b) => a * b;
    }
}
''')

    # StringUtils.cs
    (temp_dir / "StringUtils.cs").write_text('''
namespace MyApp.Utils
{
    public static class StringUtils
    {
        public static string Reverse(string s)
        {
            var chars = s.ToCharArray();
            Array.Reverse(chars);
            return new string(chars);
        }

        public static bool IsEmpty(string s) => string.IsNullOrEmpty(s);
    }
}
''')

    # Calculator.cs
    (temp_dir / "Calculator.cs").write_text('''
using MyApp.Utils;

namespace MyApp
{
    public class Calculator
    {
        public int Compute(int a, int b)
        {
            var sum = MathUtils.Add(a, b);
            var product = MathUtils.Multiply(a, b);
            return sum + product;
        }

        public string FormatResult(int result)
        {
            var text = result.ToString();
            return StringUtils.Reverse(text);
        }
    }
}
''')

    return temp_dir
