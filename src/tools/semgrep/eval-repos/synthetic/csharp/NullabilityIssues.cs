// Test file for G1, G2, G3: Nullability patterns
// Expected detections: 4 (G1, G2 x2, G3)

#nullable disable  // Expected: DD-G1-NULLABLE-DISABLED

using System;

namespace Synthetic.CSharp
{
    public class NullabilityIssues
    {
        private string _name;

        public NullabilityIssues(string name)
        {
            _name = name;
        }

        // G2: Null-forgiving operator
        public string GetNameUpper()
        {
            return _name!.ToUpper();  // Expected: DD-G2-NULL-FORGIVING-csharp
        }

        // G2: Null-forgiving on member access
        public int GetNameLength()
        {
            return _name!.Length;  // Expected: DD-G2-NULL-FORGIVING-MEMBER-csharp
        }

        // G3: Inconsistent nullable annotations
#nullable restore  // Expected: DD-G3-NULLABLE-RESTORE

        public string? GetOptionalValue()
        {
            return null;
        }
    }
}
