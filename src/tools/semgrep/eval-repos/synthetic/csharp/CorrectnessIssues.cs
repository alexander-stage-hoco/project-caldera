/**
 * Test file for CORRECTNESS_ISSUE detection.
 * Tests reference comparison, overflow, null deref, off-by-one errors.
 */

using System;
using System.Collections.Generic;

namespace SmellTests.Correctness
{
    public class CorrectnessIssues
    {
        // 1. Reference equality for strings instead of value equality
        public bool CompareStringsIncorrect(string a, string b)
        {
            // CORRECTNESS: Using == for object reference comparison
            return (object)a == (object)b;
        }

        // 2. Integer overflow in unchecked context
        public int MultiplyUnchecked(int a, int b)
        {
            // CORRECTNESS: Potential integer overflow
            return a * b;
        }

        // 3. Null dereference without check
        public int GetLength(string s)
        {
            // CORRECTNESS: Potential null dereference
            return s.Length;
        }

        // 4. Off-by-one error in loop
        public void ProcessArray(int[] arr)
        {
            // CORRECTNESS: Off-by-one - should be < arr.Length
            for (int i = 0; i <= arr.Length; i++)
            {
                Console.WriteLine(arr[i]);
            }
        }

        // 5. Double-checked locking without volatile
        private static object _instance;
        private static readonly object _lock = new object();

        public static object GetInstance()
        {
            // CORRECTNESS: Double-checked locking without volatile
            if (_instance == null)
            {
                lock (_lock)
                {
                    if (_instance == null)
                    {
                        _instance = new object();
                    }
                }
            }
            return _instance;
        }

        // GOOD: Correct string comparison
        public bool CompareStringsCorrect(string a, string b)
        {
            return string.Equals(a, b, StringComparison.Ordinal);
        }

        // GOOD: Checked arithmetic
        public int MultiplyChecked(int a, int b)
        {
            checked
            {
                return a * b;
            }
        }

        // GOOD: Null check before access
        public int GetLengthSafe(string s)
        {
            if (s == null)
                return 0;
            return s.Length;
        }

        // GOOD: Correct loop bounds
        public void ProcessArrayCorrect(int[] arr)
        {
            for (int i = 0; i < arr.Length; i++)
            {
                Console.WriteLine(arr[i]);
            }
        }
    }
}
