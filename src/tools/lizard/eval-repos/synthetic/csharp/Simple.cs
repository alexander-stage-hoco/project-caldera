// Entry point for the sample C# application
using System;

namespace SampleApp
{
    /// <summary>
    /// Main program entry point.
    /// </summary>
    public class Program
    {
        public static void Main(string[] args)
        {
            Console.WriteLine("Sample C# Application");
            Console.WriteLine("=====================");

            var service = new CalculatorService();

            // Demonstrate basic operations
            int a = 10, b = 5;
            Console.WriteLine($"Add: {a} + {b} = {service.Add(a, b)}");
            Console.WriteLine($"Subtract: {a} - {b} = {service.Subtract(a, b)}");
            Console.WriteLine($"Multiply: {a} * {b} = {service.Multiply(a, b)}");
            Console.WriteLine($"Divide: {a} / {b} = {service.Divide(a, b)}");

            // Demonstrate validation
            try
            {
                service.Divide(10, 0);
            }
            catch (DivideByZeroException ex)
            {
                Console.WriteLine($"Caught expected error: {ex.Message}");
            }

            Console.WriteLine("\nProgram completed successfully.");
        }
    }
}
