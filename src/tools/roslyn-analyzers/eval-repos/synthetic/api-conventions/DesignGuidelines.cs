using System;
using System.Collections.Generic;

namespace ApiConventions.Design
{
    /// <summary>
    /// API design guideline violations for Roslyn Analyzer testing.
    /// Expected violations: CA1002, CA1003, CA1005, CA1008, CA1010, CA1028, CA1030, CA1034
    /// </summary>
    public class DesignGuidelines
    {
        // CA1002: Do not expose generic lists - use IList<T> or ICollection<T>
        public List<string> GetItems()
        {
            return new List<string>();
        }

        // CA1002: Do not expose generic lists in properties
        public List<int> Numbers { get; set; } = new();
    }

    // CA1003: Use generic event handler instances
    public delegate void CustomEventHandler(object sender, EventArgs e);

    public class EventExample
    {
        // Should use EventHandler<TEventArgs> instead
        public event CustomEventHandler? DataChanged;

        public void OnDataChanged()
        {
            DataChanged?.Invoke(this, EventArgs.Empty);
        }
    }

    // CA1005: Avoid excessive parameters on generic types
    public class MultiGeneric<T1, T2, T3, T4, T5>  // Too many type parameters
    {
        public T1? First { get; set; }
        public T2? Second { get; set; }
        public T3? Third { get; set; }
        public T4? Fourth { get; set; }
        public T5? Fifth { get; set; }
    }

    // CA1008: Enums should have zero value
    public enum Priority
    {
        Low = 1,      // No zero value defined
        Medium = 2,
        High = 3
    }

    // CA1010: Collections should implement generic interface
    public class CustomCollection : System.Collections.IEnumerable
    {
        private readonly List<object> _items = new();

        public System.Collections.IEnumerator GetEnumerator()
        {
            return _items.GetEnumerator();
        }
    }

    // CA1028: Enum storage should be Int32
    public enum ByteEnum : byte  // Should use int
    {
        None = 0,
        First = 1,
        Second = 2
    }

    // CA1030: Use events where appropriate
    public class RaiseExample
    {
        // Method prefix 'Raise' suggests an event should be used
        public void RaiseDataChanged()
        {
            Console.WriteLine("Data changed");
        }

        // Method prefix 'Fire' suggests an event should be used
        public void FireEvent()
        {
            Console.WriteLine("Event fired");
        }
    }

    // CA1034: Nested types should not be visible
    public class OuterClass
    {
        // Public nested class - should be top-level
        public class InnerClass
        {
            public string Value { get; set; } = "";
        }

        // Another public nested class
        public class AnotherInner
        {
            public void DoWork() { }
        }
    }

    /// <summary>
    /// Clean examples that should not trigger violations
    /// </summary>
    public class CleanDesign
    {
        // Correct: Use IList<T> instead of List<T>
        public IList<string> GetItems()
        {
            return new List<string>();
        }

        // Correct: Use IReadOnlyList<T> for immutable collections
        public IReadOnlyList<int> Numbers => new List<int>();

        // Correct: Standard event pattern
        public event EventHandler<EventArgs>? ItemAdded;

        protected virtual void OnItemAdded()
        {
            ItemAdded?.Invoke(this, EventArgs.Empty);
        }
    }
}
