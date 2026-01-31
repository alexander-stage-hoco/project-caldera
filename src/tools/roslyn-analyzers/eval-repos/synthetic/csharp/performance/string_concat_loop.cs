using System;
using System.Collections.Generic;
using System.Text;

namespace SyntheticSmells.Performance
{
    /// <summary>
    /// String concatenation in loop examples for Roslyn Analyzer testing.
    /// Expected violations: Custom/CA related (3) = 3 total
    /// Note: String concat in loops is detected by various custom analyzers
    /// </summary>
    public class StringConcatLoopExamples
    {
        // String concatenation in loop - inefficient (line 16)
        public string ConcatInLoop1(List<string> items)
        {
            string result = "";
            foreach (var item in items)
            {
                result += item + ",";  // Creates new string each iteration!
            }
            return result;
        }

        // String concatenation in for loop - inefficient (line 28)
        public string ConcatInLoop2(string[] items)
        {
            string result = "";
            for (int i = 0; i < items.Length; i++)
            {
                result = result + items[i];  // O(n^2) complexity!
            }
            return result;
        }

        // String interpolation in loop - still inefficient (line 40)
        public string ConcatInLoop3(IEnumerable<int> numbers)
        {
            string result = "";
            foreach (var num in numbers)
            {
                result = $"{result}{num};";  // String interpolation still allocates!
            }
            return result;
        }

        // OK: Using StringBuilder (no violation)
        public string ConcatWithStringBuilder(List<string> items)
        {
            var sb = new StringBuilder();
            foreach (var item in items)
            {
                sb.Append(item);
                sb.Append(',');
            }
            return sb.ToString();
        }

        // OK: Using string.Join (no violation)
        public string ConcatWithJoin(List<string> items)
        {
            return string.Join(",", items);
        }

        // OK: Using string.Concat (no violation)
        public string ConcatWithConcat(string[] items)
        {
            return string.Concat(items);
        }

        // OK: Single concatenation outside loop (no violation)
        public string SimpleConcatenation(string a, string b)
        {
            return a + " " + b;  // Fine for small, fixed concatenations
        }
    }
}
