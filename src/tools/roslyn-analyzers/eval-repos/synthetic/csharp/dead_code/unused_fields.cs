using System;

namespace SyntheticSmells.DeadCode
{
    /// <summary>
    /// Unused private field examples for Roslyn Analyzer testing.
    /// Expected violations: IDE0052 (4) = 4 total
    /// </summary>
    public class UnusedFieldsExamples
    {
        // IDE0052: Private field '_unusedString' is never used (line 13)
        private string _unusedString;

        // IDE0052: Private field '_unusedCounter' is never used (line 16)
        private int _unusedCounter;

        // IDE0052: Private field '_unusedList' is never used (line 19)
        private readonly System.Collections.Generic.List<string> _unusedList = new();

        // IDE0052: Private field '_unusedFlag' is never used (line 22)
        private bool _unusedFlag;

        // Used field (no violation)
        private string _usedField;

        // Used readonly field (no violation)
        private readonly int _usedReadonly;

        public UnusedFieldsExamples(string value, int count)
        {
            _usedField = value;
            _usedReadonly = count;
        }

        public string GetValue()
        {
            return _usedField;
        }

        public int GetCount()
        {
            return _usedReadonly;
        }

        // OK: Private field assigned but never read - different analyzer
        private DateTime _assignedButNotRead;

        public void SetDate(DateTime date)
        {
            _assignedButNotRead = date;
            // This is assigned but never read - separate issue
        }

        // OK: Private field that is used
        private readonly object _lock = new();

        public void ThreadSafeOperation()
        {
            lock (_lock)
            {
                // Do something thread-safe
            }
        }
    }
}
