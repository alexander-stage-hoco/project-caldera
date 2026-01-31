// IDE0005: Unnecessary using directive (lines 2-7 are unused)
using System.Text.RegularExpressions;  // IDE0005: Never used
using System.Net.Mail;                  // IDE0005: Never used
using System.Xml;                       // IDE0005: Never used
using System.Data;                      // IDE0005: Never used
using System.Reflection;                // IDE0005: Never used
using System.Runtime.InteropServices;  // IDE0005: Never used

// These are actually used:
using System;
using System.Collections.Generic;
using System.Linq;

namespace SyntheticSmells.DeadCode
{
    /// <summary>
    /// Unused imports examples for Roslyn Analyzer testing.
    /// Expected violations: IDE0005 (6) = 6 total
    /// </summary>
    public class UnusedImportsExamples
    {
        private readonly List<string> _items = new();

        public void ProcessItems()
        {
            // Only uses System, System.Collections.Generic, and System.Linq
            var filtered = _items.Where(x => !string.IsNullOrEmpty(x)).ToList();
            Console.WriteLine($"Processed {filtered.Count} items");
        }

        public int SumValues(IEnumerable<int> values)
        {
            return values.Sum();
        }

        public DateTime GetCurrentTime()
        {
            return DateTime.UtcNow;
        }
    }
}
