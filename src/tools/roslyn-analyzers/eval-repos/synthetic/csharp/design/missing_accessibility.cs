using System;

namespace SyntheticSmells.Design
{
    /// <summary>
    /// Missing accessibility modifier examples for Roslyn Analyzer testing.
    /// Expected violations: IDE0040 (5) = 5 total
    /// </summary>

    // IDE0040: Class without explicit accessibility (line 11)
    class ImplicitInternalClass
    {
        // IDE0040: Method without explicit accessibility (line 14)
        void ImplicitPrivateMethod()
        {
        }

        // IDE0040: Property without explicit accessibility (line 19)
        int ImplicitPrivateProperty { get; set; }

        // IDE0040: Field without explicit accessibility (line 22)
        string implicitPrivateField;

        // IDE0040: Event without explicit accessibility (line 25)
        event EventHandler ImplicitPrivateEvent;

        // OK: Explicit private
        private void ExplicitPrivateMethod() { }
        private int ExplicitPrivateProperty { get; set; }
        private string explicitPrivateField;
    }

    // OK: Explicit internal class
    internal class ExplicitInternalClass
    {
        public void PublicMethod() { }
        private void PrivateMethod() { }
        internal void InternalMethod() { }
        protected void ProtectedMethod() { }
    }

    // OK: Public class with explicit modifiers
    public class ExplicitPublicClass
    {
        public string Name { get; set; }
        private int _count;
        internal bool IsValid { get; }
        protected virtual void OnChange() { }
    }

    // OK: Interface members are implicitly public
    public interface IExplicitInterface
    {
        void DoSomething();  // Implicitly public - this is OK
        string Name { get; }
    }

    // OK: Enum members are implicitly public
    public enum ExplicitEnum
    {
        Value1,  // Implicitly public - this is OK
        Value2
    }
}
