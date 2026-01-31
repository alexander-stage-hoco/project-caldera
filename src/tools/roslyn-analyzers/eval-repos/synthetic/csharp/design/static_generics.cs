using System;

namespace SyntheticSmells.Design
{
    /// <summary>
    /// Static members on generic types examples for Roslyn Analyzer testing.
    /// Expected violations: CA1000 (3) = 3 total
    /// </summary>

    // CA1000: Static method on generic type (line 11)
    public class GenericWithStatic<T>
    {
        // This requires GenericWithStatic<SomeType>.Create() syntax
        // which is awkward and potentially confusing
        public static T Create()
        {
            return default(T);
        }

        // CA1000: Static property on generic type (line 21)
        public static T Default { get; } = default(T);

        // CA1000: Static field on generic type (line 24)
        public static int InstanceCount = 0;

        // OK: Instance members on generic types are fine
        public T Value { get; set; }
        public void Process(T item) { }
    }

    // Example showing the confusion
    public class StaticGenericConfusion
    {
        public void DemonstrateConfusion()
        {
            // Each closed generic type has its own static members!
            GenericWithStatic<int>.InstanceCount = 1;
            GenericWithStatic<string>.InstanceCount = 2;
            // These are DIFFERENT static fields!

            // This syntax is awkward
            var intDefault = GenericWithStatic<int>.Create();
            var strDefault = GenericWithStatic<string>.Create();
        }
    }

    // Better: Factory pattern with non-generic static class
    public static class GenericFactory
    {
        public static GenericClass<T> Create<T>()
        {
            return new GenericClass<T>();
        }
    }

    public class GenericClass<T>
    {
        public T Value { get; set; }
    }

    // Another good pattern: static inner class
    public class GenericContainer<T>
    {
        public T Item { get; set; }

        // OK: Nested non-generic static class
        public static class Factory
        {
            // This is a cleaner pattern
        }
    }
}
