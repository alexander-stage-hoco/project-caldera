using System;

namespace SyntheticSmells.DeadCode
{
    /// <summary>
    /// Unused local variable examples for Roslyn Analyzer testing.
    /// Expected violations: IDE0059 (4) = 4 total
    /// </summary>
    public class UnusedLocalsExamples
    {
        // IDE0059: Local variable 'unused' is never used (line 14)
        public void Method1()
        {
            var unused = "hello";
            Console.WriteLine("World");
            // unused is declared but never used!
        }

        // IDE0059: Local variable 'counter' is never used (line 23)
        public int Method2(int input)
        {
            int counter = 0;
            return input * 2;
            // counter is declared but never used!
        }

        // IDE0059: Local variable 'result' is never used (line 32)
        public void Method3()
        {
            var items = new int[] { 1, 2, 3 };
            var result = items.Length;
            Console.WriteLine(items);
            // result is computed but never used!
        }

        // IDE0059: Unused assignment (line 41)
        public int Method4(int x)
        {
            int temp = x + 1;
            temp = x * 2;  // Previous assignment never used!
            return temp;
        }

        // OK: Variable is used (no violation)
        public void UsedLocalVariable()
        {
            var message = "Hello";
            Console.WriteLine(message);
        }

        // OK: Variable computed and returned (no violation)
        public int ComputeAndReturn(int x)
        {
            var result = x * x;
            return result;
        }

        // OK: Variable used in conditional (no violation)
        public void ConditionalUsage(int x)
        {
            var threshold = 10;
            if (x > threshold)
            {
                Console.WriteLine("Above threshold");
            }
        }

        // OK: Discards are intentional (no violation for explicit discard)
        public void DiscardExample()
        {
            _ = int.TryParse("123", out _);  // Intentional discard
        }
    }
}
