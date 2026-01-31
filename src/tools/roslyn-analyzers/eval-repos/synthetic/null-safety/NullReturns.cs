using System;
using System.Collections.Generic;
using System.Linq;

namespace NullSafety.Returns
{
    /// <summary>
    /// Possible null return violations.
    /// Expected violations: CS8603 (Possible null reference return), CS8600 (Converting null literal)
    /// </summary>
    public class NullReturnExamples
    {
        // CS8603: Possible null reference return
        public string GetName(bool condition)
        {
            if (condition)
            {
                return "Name";
            }
            return null;  // Returns null from non-nullable return type
        }

        // CS8603: Returning nullable from non-nullable
        public string GetValue(string? input)
        {
            return input;  // Returning nullable as non-nullable
        }

        // CS8603: LINQ FirstOrDefault returns nullable
        public string FindItem(List<string> items, string search)
        {
            return items.FirstOrDefault(x => x == search);  // May return null
        }

        // CS8603: Dictionary lookup may return null
        public string GetFromDictionary(Dictionary<string, string> dict, string key)
        {
            if (dict.TryGetValue(key, out var value))
            {
                return value;
            }
            return null;  // Returns null from non-nullable
        }
    }

    public class NullConversionExamples
    {
        // CS8600: Converting null literal to non-nullable type
        public void ConvertNullLiteral()
        {
            string name = null;  // CS8600
            Console.WriteLine(name);
        }

        // CS8600: Converting nullable to non-nullable
        public void ConvertNullable(string? nullable)
        {
            string nonNullable = nullable;  // CS8600
            Console.WriteLine(nonNullable);
        }

        // CS8600: Implicit conversion in assignment
        public void ImplicitConversion()
        {
            string? maybeNull = GetMaybeNull();
            string definitelyNotNull = maybeNull;  // CS8600
            Console.WriteLine(definitelyNotNull);
        }

        private string? GetMaybeNull() => Random.Shared.NextDouble() > 0.5 ? "value" : null;
    }

    /// <summary>
    /// Clean null-safe return patterns
    /// </summary>
    public class SafeReturnExamples
    {
        // OK: Nullable return type
        public string? GetNameSafe(bool condition)
        {
            if (condition)
            {
                return "Name";
            }
            return null;
        }

        // OK: Null coalescing for default value
        public string GetValueSafe(string? input)
        {
            return input ?? "default";
        }

        // OK: Using nullable return type for LINQ
        public string? FindItemSafe(List<string> items, string search)
        {
            return items.FirstOrDefault(x => x == search);
        }
    }
}
