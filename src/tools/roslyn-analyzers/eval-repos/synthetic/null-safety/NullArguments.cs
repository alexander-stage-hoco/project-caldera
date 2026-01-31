using System;
using System.Collections.Generic;

namespace NullSafety.Arguments
{
    /// <summary>
    /// Null argument violations and CA1062 (validate arguments) issues.
    /// Expected violations: CS8604, CA1062
    /// </summary>
    public class NullArgumentExamples
    {
        // CS8604: Possible null reference argument for parameter
        public void PassNullableAsNonNullable(string? maybeNull)
        {
            ProcessNonNullable(maybeNull);  // CS8604
        }

        public void ProcessNonNullable(string value)
        {
            Console.WriteLine(value.Length);
        }

        // CS8604: Multiple null argument violations
        public void MultipleNullArgs(string? a, string? b, string? c)
        {
            CombineStrings(a, b, c);  // CS8604 for all three
        }

        public string CombineStrings(string first, string second, string third)
        {
            return first + second + third;
        }

        // CS8604: Null to collection
        public void AddToList(List<string> list, string? item)
        {
            list.Add(item);  // CS8604: item may be null
        }
    }

    public class MissingArgumentValidation
    {
        // CA1062: Validate parameter before use
        public void ProcessData(string[] data)
        {
            // Missing null check - CA1062
            foreach (var item in data)
            {
                Console.WriteLine(item);
            }
        }

        // CA1062: Multiple parameters without validation
        public void CopyData(byte[] source, byte[] destination)
        {
            // Neither parameter is validated
            Array.Copy(source, destination, source.Length);
        }

        // CA1062: Object parameter without validation
        public void UseObject(IDisposable resource)
        {
            // Missing null check
            resource.Dispose();
        }

        // CA1062: Collection parameter without validation
        public int CountItems(ICollection<string> items)
        {
            // Missing null check
            return items.Count;
        }
    }

    /// <summary>
    /// Clean argument handling patterns
    /// </summary>
    public class SafeArgumentExamples
    {
        // OK: Null check with exception
        public void ProcessData(string[] data)
        {
            ArgumentNullException.ThrowIfNull(data);
            foreach (var item in data)
            {
                Console.WriteLine(item);
            }
        }

        // OK: Defensive null check
        public void ProcessWithCheck(string? value)
        {
            if (value != null)
            {
                ProcessNonNullable(value);  // OK after check
            }
        }

        private void ProcessNonNullable(string value)
        {
            Console.WriteLine(value);
        }

        // OK: Null coalescing for default
        public void ProcessWithDefault(string? value)
        {
            string safe = value ?? "default";
            Console.WriteLine(safe);
        }
    }
}
