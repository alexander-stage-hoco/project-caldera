// Test file for H6, H8: Static mutable state and dynamic usage
// Expected detections: 4 (H6 x2, H8 x2)

using System;
using System.Collections.Generic;

namespace Synthetic.CSharp
{
    public class StaticState
    {
        // H6: Private static mutable state - BAD
        private static int _counter = 0;  // Expected: DD-H6-STATIC-MUTABLE-STATE-csharp

        // H6: Public static mutable state - WORSE
        public static string GlobalConfig = "default";  // Expected: DD-H6-PUBLIC-STATIC-MUTABLE-csharp

        // GOOD: Static readonly is fine
        private static readonly int MaxRetries = 3;

        // H8: Dynamic type usage - BAD
        public void ProcessDynamicData()
        {
            dynamic data = GetData();  // Expected: DD-H8-DYNAMIC-USAGE-csharp
            Console.WriteLine(data.Name);
        }

        // H8: Dynamic parameter in public method - BAD
        public void HandleDynamicInput(dynamic input)  // Expected: DD-H8-DYNAMIC-PARAM-csharp
        {
            Console.WriteLine(input.ToString());
        }

        private object GetData()
        {
            return new { Name = "Test" };
        }

        public static void IncrementCounter()
        {
            _counter++;
        }
    }
}
