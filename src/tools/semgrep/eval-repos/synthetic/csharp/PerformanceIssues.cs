/**
 * Test file for PERFORMANCE_ISSUE detection.
 * Tests string concat loop, Count() vs Any(), uncached regex.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

namespace SmellTests.Performance
{
    public class PerformanceIssues
    {
        // 1. String concatenation in loop
        public string BuildStringInefficient(IEnumerable<string> items)
        {
            // PERFORMANCE: String concat in loop creates many intermediate strings
            string result = "";
            foreach (var item in items)
            {
                result += item + ",";
            }
            return result;
        }

        // 2. Using Count() when Any() would suffice
        public bool HasItemsInefficient(IEnumerable<int> items)
        {
            // PERFORMANCE: Count() iterates entire collection
            return items.Count() > 0;
        }

        // 3. Regex not cached
        public bool MatchesPatternInefficient(string input)
        {
            // PERFORMANCE: Regex.IsMatch compiles pattern each call
            return Regex.IsMatch(input, @"\d{4}-\d{2}-\d{2}");
        }

        // 4. LINQ query in loop
        public List<int> FilterInLoop(List<int> items, int[] thresholds)
        {
            var results = new List<int>();
            // PERFORMANCE: LINQ query executed multiple times in loop
            foreach (var threshold in thresholds)
            {
                results.AddRange(items.Where(x => x > threshold));
            }
            return results;
        }

        // 5. Boxing in loop
        public void ProcessNumbers(int[] numbers)
        {
            // PERFORMANCE: Boxing integers in loop
            var list = new List<object>();
            foreach (var n in numbers)
            {
                list.Add(n);  // Boxing occurs here
            }
        }

        // GOOD: StringBuilder for string building
        public string BuildStringCorrect(IEnumerable<string> items)
        {
            var sb = new StringBuilder();
            foreach (var item in items)
            {
                sb.Append(item).Append(',');
            }
            return sb.ToString();
        }

        // GOOD: Use Any() for existence check
        public bool HasItemsCorrect(IEnumerable<int> items)
        {
            return items.Any();
        }

        // GOOD: Cached regex
        private static readonly Regex DatePattern = new Regex(
            @"\d{4}-\d{2}-\d{2}",
            RegexOptions.Compiled);

        public bool MatchesPatternCorrect(string input)
        {
            return DatePattern.IsMatch(input);
        }

        // GOOD: Generic list to avoid boxing
        public void ProcessNumbersCorrect(int[] numbers)
        {
            var list = new List<int>();
            foreach (var n in numbers)
            {
                list.Add(n);  // No boxing
            }
        }
    }
}
