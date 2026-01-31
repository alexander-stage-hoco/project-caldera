using System;

namespace SyntheticSmells.Design
{
    /// <summary>
    /// Visible instance field examples for Roslyn Analyzer testing.
    /// Expected violations: CA1051 (5) = 5 total
    /// </summary>
    public class VisibleFieldsExamples
    {
        // CA1051: Public instance field (line 13)
        public string Name;

        // CA1051: Public instance field (line 16)
        public int Age;

        // CA1051: Public instance field (line 19)
        public DateTime CreatedAt;

        // CA1051: Protected instance field in non-sealed class (line 22)
        protected double Balance;

        // CA1051: Internal instance field (line 25)
        internal bool IsActive;

        // OK: Public static field (no violation)
        public static readonly string DefaultName = "Unknown";

        // OK: Public const field (no violation)
        public const int MaxAge = 150;

        // OK: Private field (no violation)
        private string _privateField;

        // OK: Field in struct (no violation for public fields in structs)
        // Structs are value types and often need public fields

        // OK: Property instead of field (recommended pattern)
        public string Email { get; set; }
        public int Id { get; private set; }
    }

    // Additional class with visible fields
    public class AnotherVisibleFieldsClass
    {
        // These should all be properties instead
        public object Data;          // OK to have reference types as fields if needed
        public decimal Price;        // But public instance fields are still discouraged
    }

    // Sealed class - protected fields OK since can't be inherited
    public sealed class SealedClass
    {
        protected int Value;  // OK in sealed class, but still a smell in general design
    }
}
