// Test file for B2_LONG_PARAMETER_LIST
// Expected detections: 2 (method with 6 params, constructor with 7 params)

using System;

namespace Synthetic.CSharp
{
    public class OrderRequest { }

    public class LongParameterListExamples
    {
        // BAD: 6 parameters - Expected: DD-B2-LONG-PARAM-LIST-6-csharp
        public void ProcessOrder(string id, string name, decimal price,
            int quantity, DateTime date, string notes)
        {
            Console.WriteLine($"Processing: {id}");
        }

        // BAD: 7 parameters in constructor - Expected: DD-B2-LONG-CTOR-PARAMS-csharp
        public LongParameterListExamples(string a, string b, string c,
            string d, string e, string f, string g)
        {
            Console.WriteLine("Constructor with many params");
        }

        // GOOD: 5 parameters (under threshold)
        public void ValidMethod(string a, string b, string c, string d, string e)
        {
            Console.WriteLine("Only 5 params - acceptable");
        }

        // GOOD: 4 parameters
        public void AnotherValidMethod(string a, int b, bool c, DateTime d)
        {
            Console.WriteLine("Only 4 params");
        }

        // GOOD: Using parameter object pattern
        public void ProcessOrderGood(OrderRequest request)
        {
            Console.WriteLine("Using parameter object - good pattern");
        }

        // GOOD: Private method with many params (not public API)
        private void InternalHelper(string a, string b, string c, string d, string e, string f, string g)
        {
            Console.WriteLine("Private method - less concerning");
        }
    }
}
