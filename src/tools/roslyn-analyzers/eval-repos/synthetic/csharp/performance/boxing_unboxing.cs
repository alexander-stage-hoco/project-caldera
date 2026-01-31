using System;
using System.Collections;
using System.Collections.Generic;

namespace SyntheticSmells.Performance
{
    /// <summary>
    /// Value type boxing/unboxing examples for Roslyn Analyzer testing.
    /// Expected violations: Custom boxing detection (4) = 4 total
    /// Note: Boxing is detected by various performance analyzers
    /// </summary>
    public class BoxingUnboxingExamples
    {
        // Boxing: value type assigned to object (line 16)
        public object BoxInteger(int value)
        {
            return value;  // Boxing occurs here!
        }

        // Boxing: value type in non-generic collection (line 23)
        public void AddToArrayList(ArrayList list, int value)
        {
            list.Add(value);  // Boxing occurs!
        }

        // Boxing: value type in string interpolation with interface (line 30)
        public string FormatValue(IFormattable formattable)
        {
            int value = 42;
            return string.Format("{0}", (IFormattable)value);  // Boxing!
        }

        // Boxing: struct implementing interface cast (line 38)
        public void ProcessEnumerable(IEnumerable<MyStruct> items)
        {
            foreach (var item in items)
            {
                IEquatable<MyStruct> equatable = item;  // Boxing!
                equatable.Equals(default);
            }
        }

        // OK: Generic collection avoids boxing (no violation)
        public void AddToGenericList(List<int> list, int value)
        {
            list.Add(value);  // No boxing with generics
        }

        // OK: Value type stays as value type (no violation)
        public int ProcessInteger(int value)
        {
            return value * 2;
        }

        // OK: Using generic interface constraint (no violation)
        public bool CompareGeneric<T>(T a, T b) where T : IEquatable<T>
        {
            return a.Equals(b);  // No boxing due to constraint
        }

        // OK: String interpolation with value type (usually optimized)
        public string InterpolateValue(int value)
        {
            return $"Value: {value}";  // Modern compiler optimizes this
        }
    }

    public struct MyStruct : IEquatable<MyStruct>
    {
        public int Value { get; set; }

        public bool Equals(MyStruct other)
        {
            return Value == other.Value;
        }
    }
}
