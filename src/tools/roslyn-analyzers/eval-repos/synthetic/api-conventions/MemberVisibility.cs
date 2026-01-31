using System;

namespace ApiConventions.Visibility
{
    /// <summary>
    /// Member visibility and accessibility violations.
    /// Expected violations: CA1019, CA1024, CA1044, CA1051, CA1052
    /// </summary>

    // Custom attribute with accessibility issues
    [AttributeUsage(AttributeTargets.Class)]
    public class CustomAttribute : Attribute
    {
        // CA1019: Define accessors for attribute arguments
        public CustomAttribute(string name, int value)
        {
            Name = name;
            // Value parameter has no corresponding property
        }

        public string Name { get; }
        // Missing: public int Value { get; }
    }

    public class PropertyMethodConfusion
    {
        private string _data = "";
        private int _count;

        // CA1024: Use properties where appropriate
        // This should be a property since it's a simple getter
        public string GetData()
        {
            return _data;
        }

        // CA1024: Another getter that should be a property
        public int GetCount()
        {
            return _count;
        }

        // OK: Method with parameters cannot be a property
        public string GetDataWithFormat(string format)
        {
            return string.Format(format, _data);
        }
    }

    public class WriteOnlyProperties
    {
        private string _secret = "";
        private int _code;

        // CA1044: Properties should not be write only
        public string Secret
        {
            set { _secret = value; }
        }

        // CA1044: Another write-only property
        public int Code
        {
            set { _code = value; }
        }
    }

    public class VisibleFields
    {
        // CA1051: Do not declare visible instance fields
        public string Name;
        public int Age;
        protected decimal Salary;

        // OK: Static fields are acceptable
        public static readonly string DefaultName = "Unknown";

        // OK: Const fields are acceptable
        public const int MaxAge = 150;

        // OK: Private fields
        private string _privateField = "";
    }

    // CA1052: Static holder types should be static or sealed
    public class UtilityClass
    {
        // All static members but class is not static/sealed
        public static void DoSomething() { }
        public static string GetValue() => "value";
        public static readonly int Constant = 42;
    }

    // Clean example
    public static class CleanUtility
    {
        public static void DoSomething() { }
        public static string GetValue() => "value";
    }
}
