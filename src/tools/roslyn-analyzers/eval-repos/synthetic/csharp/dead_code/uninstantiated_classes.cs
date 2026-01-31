using System;

namespace SyntheticSmells.DeadCode
{
    /// <summary>
    /// Uninstantiated internal class examples for Roslyn Analyzer testing.
    /// Expected violations: CA1812 (3) = 3 total
    /// </summary>

    // CA1812: Internal class that is never instantiated (line 11)
    internal class NeverInstantiated1
    {
        public void DoSomething()
        {
            Console.WriteLine("This method is never called");
        }

        public int Calculate(int x)
        {
            return x * 2;
        }
    }

    // CA1812: Internal class with constructor that is never called (line 26)
    internal class NeverInstantiated2
    {
        private readonly string _data;

        public NeverInstantiated2(string data)
        {
            _data = data;
        }

        public string GetData() => _data;
    }

    // CA1812: Internal helper class never used (line 40)
    internal class DeadHelperClass
    {
        public static int Add(int a, int b) => a + b;
        public static int Subtract(int a, int b) => a - b;
        public static int Multiply(int a, int b) => a * b;
    }

    // OK: Public class (no violation - may be used externally)
    public class PublicClass
    {
        public void DoSomething() { }
    }

    // OK: Internal class that is instantiated
    internal class InstantiatedClass
    {
        public string Name { get; set; }
    }

    // OK: Abstract class - cannot be instantiated directly
    internal abstract class AbstractClass
    {
        public abstract void DoSomething();
    }

    // OK: Static class - not meant to be instantiated
    internal static class StaticHelper
    {
        public static int Add(int a, int b) => a + b;
    }

    // Class that instantiates InstantiatedClass
    public class ClassUser
    {
        public void UseClasses()
        {
            var instance = new InstantiatedClass();
            instance.Name = "Test";
            Console.WriteLine(instance.Name);
        }
    }

    // OK: Internal class used via DI container (may need attribute)
    [UsedByDI]
    internal class ServiceClass
    {
        public void Serve() { }
    }

    // Attribute to mark DI-used classes
    [AttributeUsage(AttributeTargets.Class)]
    public class UsedByDIAttribute : Attribute { }
}
