using System;
using System.Collections.Generic;

namespace SyntheticSmells.Performance
{
    /// <summary>
    /// Unnecessary array allocation examples for Roslyn Analyzer testing.
    /// Expected violations: CA1825 (4) = 4 total
    /// </summary>
    public class EmptyArrayAllocExamples
    {
        // CA1825: Avoid zero-length array allocations (line 14)
        public int[] GetEmptyArray1()
        {
            return new int[0];
            // Should use Array.Empty<int>()
        }

        // CA1825: Avoid zero-length array allocations (line 22)
        public string[] GetEmptyArray2()
        {
            return new string[] { };
            // Should use Array.Empty<string>()
        }

        // CA1825: Avoid creating empty array as default (line 30)
        public byte[] GetDefaultBuffer()
        {
            return new byte[0];
            // Should use Array.Empty<byte>()
        }

        // CA1825: Empty array in method call (line 38)
        public void ProcessData()
        {
            DoSomething(new object[0]);
            // Should use Array.Empty<object>()
        }

        private void DoSomething(object[] items) { }

        // OK: Using Array.Empty<T>() (no violation)
        public int[] GetEmptyArrayProper1()
        {
            return Array.Empty<int>();
        }

        // OK: Using Array.Empty<T>() (no violation)
        public string[] GetEmptyArrayProper2()
        {
            return Array.Empty<string>();
        }

        // OK: Non-empty array allocation (no violation)
        public int[] GetNonEmptyArray()
        {
            return new int[] { 1, 2, 3 };
        }

        // OK: Sized array allocation (no violation)
        public byte[] GetBuffer(int size)
        {
            return new byte[size];
        }
    }
}
