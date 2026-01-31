using System;
using System.Collections.Generic;

namespace NullSafety.Dereference
{
    /// <summary>
    /// Possible null dereference violations.
    /// Expected violations: CS8602 (Dereference of a possibly null reference)
    /// </summary>
    public class NullDereferenceExamples
    {
        public void UnsafeDereference(string? input)
        {
            // CS8602: Dereference of possibly null reference
            int length = input.Length;
            Console.WriteLine(length);
        }

        public void UnsafeMethodCall(object? obj)
        {
            // CS8602: Calling method on possibly null reference
            string text = obj.ToString();
            Console.WriteLine(text);
        }

        public string? GetValue() => null;

        public void ChainedDereference()
        {
            string? value = GetValue();
            // CS8602: Possible null dereference
            string upper = value.ToUpper();
            Console.WriteLine(upper);
        }

        public void CollectionAccess(Dictionary<string, string>? dict)
        {
            // CS8602: Possible null dereference on dictionary access
            string value = dict["key"];
            Console.WriteLine(value);
        }

        public void ArrayAccess(string[]? items)
        {
            // CS8602: Possible null dereference on array access
            string first = items[0];
            Console.WriteLine(first);
        }

        public void PropertyChain(Container? container)
        {
            // CS8602: Possible null dereference on property chain
            string name = container.Inner.Name;
            Console.WriteLine(name);
        }
    }

    public class Container
    {
        public Inner Inner { get; set; } = new();
    }

    public class Inner
    {
        public string Name { get; set; } = "";
    }

    /// <summary>
    /// Clean null-safe patterns
    /// </summary>
    public class SafeDereferenceExamples
    {
        public void SafeNullCheck(string? input)
        {
            // OK: Explicit null check
            if (input != null)
            {
                int length = input.Length;
                Console.WriteLine(length);
            }
        }

        public void SafeNullConditional(string? input)
        {
            // OK: Null-conditional operator
            int? length = input?.Length;
            Console.WriteLine(length ?? 0);
        }

        public void SafePatternMatching(object? obj)
        {
            // OK: Pattern matching
            if (obj is string text)
            {
                Console.WriteLine(text.ToUpper());
            }
        }
    }
}
