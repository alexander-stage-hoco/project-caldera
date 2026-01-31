using System;
using System.Collections.Generic;
using System.Linq;

namespace SyntheticSmells.Performance
{
    /// <summary>
    /// Inefficient LINQ pattern examples for Roslyn Analyzer testing.
    /// Expected violations: CA1826 (3), CA1829 (2) = 5 total
    /// </summary>
    public class InefficientLinqExamples
    {
        // CA1826: Use First() instead of Single() when appropriate (line 15)
        public int GetFirstItem(List<int> items)
        {
            return items.Where(x => x > 0).Single();
            // Could use First() if we know there's exactly one
        }

        // CA1826: OrderBy before First (line 23)
        public string GetOldestName(List<Person> people)
        {
            return people.OrderBy(p => p.Age).Last().Name;
            // OrderByDescending + First is more efficient
        }

        // CA1826: Redundant ToList before Count (line 31)
        public int CountActive(IEnumerable<Person> people)
        {
            return people.Where(p => p.IsActive).ToList().Count();
            // Count() on IEnumerable is more efficient
        }

        // CA1829: Use Length instead of Count() on array (line 39)
        public int GetArrayCount(int[] items)
        {
            return items.Count();
            // Should use items.Length
        }

        // CA1829: Use Count property instead of Count() on List (line 47)
        public int GetListCount(List<string> items)
        {
            return items.Count();
            // Should use items.Count
        }

        // OK: Proper First usage (no violation)
        public int GetFirstItemProper(List<int> items)
        {
            return items.Where(x => x > 0).First();
        }

        // OK: Using Count property (no violation)
        public int GetListCountProper(List<string> items)
        {
            return items.Count;
        }

        // OK: Using Length property (no violation)
        public int GetArrayCountProper(int[] items)
        {
            return items.Length;
        }
    }

    public class Person
    {
        public string Name { get; set; }
        public int Age { get; set; }
        public bool IsActive { get; set; }
    }
}
