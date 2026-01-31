using System;
using System.Collections.Generic;
using System.IO;

namespace SyntheticSmells.Design
{
    /// <summary>
    /// CA1061: Do not hide base class methods
    /// CA1061 fires when a derived method has the same name but parameter types
    /// that are MORE WEAKLY DERIVED (less specific) than the base method.
    /// Expected violations: CA1061 (4) = 4 total
    /// </summary>

    // Base class with specific parameter types
    public class InheritanceBaseClass
    {
        // Methods with specific parameter types
        public void ProcessItems(IList<string> items) { }
        public void HandleData(string data) { }
        public void ExecuteCommand(ArgumentException error) { }
        public void SendMessage(FileNotFoundException ex) { }
    }

    // CA1061: Derived class hides base methods with weaker parameter types
    public class InheritanceDerivedClass : InheritanceBaseClass
    {
        // CA1061: IEnumerable<string> is weaker than IList<string>
        public void ProcessItems(IEnumerable<string> items)
        {
            // This hides base.ProcessItems(IList<string>)
        }

        // CA1061: object is weaker than string
        public void HandleData(object data)
        {
            // This hides base.HandleData(string)
        }

        // CA1061: Exception is weaker than ArgumentException
        public void ExecuteCommand(Exception error)
        {
            // This hides base.ExecuteCommand(ArgumentException)
        }

        // CA1061: Exception is weaker than FileNotFoundException
        public void SendMessage(Exception ex)
        {
            // This hides base.SendMessage(FileNotFoundException)
        }
    }

    // OK: Properly extending without hiding
    public class ProperInheritanceDerivedClass : InheritanceBaseClass
    {
        // Different method name - no hiding
        public void ProcessAllItems(IEnumerable<string> items) { }

        // Different parameter count - no hiding
        public void HandleData(string data, bool validate) { }

        // More specific parameter - no hiding (overloading is fine)
        public void ExecuteCommand(InvalidOperationException error) { }
    }

    // Additional inheritance anti-patterns for detection

    // Base with generic constraints
    public class GenericBaseClass<T> where T : class
    {
        public void Process(T item) { }
        public void Handle(ICollection<T> items) { }
    }

    // CA1061 can also fire in generic scenarios
    public class GenericDerivedClass : GenericBaseClass<string>
    {
        // Hiding with weaker type
        public void Process(object item)
        {
            // Hides base.Process(string)
        }

        // Hiding with weaker collection type
        public void Handle(IEnumerable<string> items)
        {
            // Hides base.Handle(ICollection<string>)
        }
    }

    // Deep inheritance chain example
    public class Level1Base
    {
        public void Execute(InvalidOperationException ex) { }
    }

    public class Level2Middle : Level1Base
    {
        // OK - same signature
    }

    public class Level3Derived : Level2Middle
    {
        // Hides method from Level1Base with weaker type
        public void Execute(Exception ex)
        {
            // CA1061: Hides Level1Base.Execute(InvalidOperationException)
        }
    }
}
