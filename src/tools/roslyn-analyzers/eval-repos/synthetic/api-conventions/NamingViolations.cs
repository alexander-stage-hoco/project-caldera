using System;
using System.Threading.Tasks;

namespace ApiConventions.Naming
{
    /// <summary>
    /// API naming convention violations for Roslyn Analyzer testing.
    /// Expected violations: CA1707, CA1708, CA1710, CA1715, CA1716, CA1720, CA1724
    /// </summary>
    public class naming_violations  // CA1707: Remove underscores from type name
    {
        // CA1707: Remove underscores from member name
        public string User_Name { get; set; } = "";

        // CA1707: Remove underscores from member name
        public void Process_Data() { }

        // CA1720: Identifier contains type name
        public int IntValue { get; set; }

        // CA1720: Identifier contains type name
        public string StringData { get; set; } = "";
    }

    // CA1710: Identifiers should have correct suffix
    public class UserList : System.Collections.Generic.List<string>
    {
        // Should be named UserCollection
    }

    // CA1715: Identifiers should have correct prefix
    public interface Serializable  // Should start with 'I'
    {
        void Serialize();
    }

    // CA1716: Identifiers should not match keywords
    public class Error  // 'Error' is a reserved word in some languages
    {
        public string Message { get; set; } = "";
    }

    // CA1724: Type names should not match namespaces
    public class System  // Conflicts with System namespace
    {
        public void DoSomething() { }
    }

    /// <summary>
    /// Additional naming issues
    /// </summary>
    public class MoreNamingIssues
    {
        // CA1708: Identifiers should differ by more than case
        public string DATA { get; set; } = "";
        public string data { get; set; } = "";  // Differs only by case

        // CA1707: Remove underscores
        public const string DEFAULT_VALUE = "default";

        // Method with underscore
        public void Get_All_Items() { }
    }
}
