// Test file for I2_UNREACHABLE_CODE
// Expected detections: 2 (code after return, code after throw)

using System;

namespace Synthetic.CSharp
{
    public class UnreachableCodeExamples
    {
        private object _logger = new object();

        // BAD: Code after return - Expected: DD-I2-UNREACHABLE-AFTER-RETURN-csharp
        public int GetValue()
        {
            return 42;
            Console.WriteLine("This code is never reached");
        }

        // BAD: Code after throw - Expected: DD-I2-UNREACHABLE-AFTER-THROW-csharp
        public void Validate(string input)
        {
            if (input == null)
            {
                throw new ArgumentNullException(nameof(input));
                Console.WriteLine("This is dead code");
            }
            Console.WriteLine("Valid input received");
        }

        // GOOD: No unreachable code - return at end
        public int GetValueGood()
        {
            var result = Calculate();
            Console.WriteLine($"Result: {result}");
            return result;
        }

        // GOOD: Early return pattern (code before return is reachable)
        public int EarlyReturn(int x)
        {
            if (x < 0)
            {
                Console.WriteLine("Negative value");
                return -1;
            }
            Console.WriteLine("Positive value");
            return x * 2;
        }

        // GOOD: Code after conditional throw (outer code is reachable)
        public void ValidateWithLog(string input)
        {
            if (input == null)
            {
                throw new ArgumentNullException(nameof(input));
            }
            // This code IS reachable when input is not null
            Console.WriteLine($"Processing: {input}");
        }

        private int Calculate() => 100;
    }
}
