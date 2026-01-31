using System;

namespace SyntheticSmells.Design
{
    /// <summary>
    /// Empty interface examples for Roslyn Analyzer testing.
    /// Expected violations: CA1040 (3) = 3 total
    /// </summary>

    // CA1040: Empty interface (line 11)
    public interface IEmpty
    {
    }

    // CA1040: Empty marker interface (line 16)
    public interface IMarker
    {
        // No members - used as a marker
    }

    // CA1040: Empty interface extending another empty interface (line 22)
    public interface IEmptyChild : IEmpty
    {
        // Still empty
    }

    // OK: Interface with members (no violation)
    public interface IHasMembers
    {
        void DoSomething();
        string Name { get; }
    }

    // OK: Interface inheriting members (no violation)
    public interface IHasInheritedMembers : IHasMembers
    {
        void DoSomethingElse();
    }

    // OK: Generic interface with constraint (arguably not empty)
    public interface IGenericMarker<T> where T : class
    {
    }

    // Example usage showing why empty interfaces are problematic
    public class EmptyInterfaceUser
    {
        // This pattern is fragile - use attributes instead
        public void ProcessMarked(object obj)
        {
            if (obj is IMarker)
            {
                // Do something special - but why use an interface?
                // Attributes are better for metadata
            }
        }
    }

    // Better alternative: use an attribute
    [AttributeUsage(AttributeTargets.Class)]
    public class MarkerAttribute : Attribute { }

    [Marker]
    public class BetterMarkedClass { }
}
