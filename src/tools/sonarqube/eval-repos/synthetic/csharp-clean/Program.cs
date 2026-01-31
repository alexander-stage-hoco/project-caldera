namespace CleanCode;

/// <summary>
/// Main entry point for the application.
/// </summary>
public class Program
{
    public static void Main(string[] args)
    {
        var calculator = new Calculator();

        Console.WriteLine("Calculator Demo");
        Console.WriteLine($"2 + 3 = {calculator.Add(2, 3)}");
        Console.WriteLine($"10 - 4 = {calculator.Subtract(10, 4)}");
        Console.WriteLine($"5 * 6 = {calculator.Multiply(5, 6)}");
        Console.WriteLine($"15 / 3 = {calculator.Divide(15, 3)}");

        Console.WriteLine("\nString Utils Demo");
        Console.WriteLine($"Reverse 'hello': {StringUtils.Reverse("hello")}");
        Console.WriteLine($"Capitalize 'world': {StringUtils.Capitalize("world")}");
        Console.WriteLine($"Word count 'hello world': {StringUtils.CountWords("hello world")}");
    }
}
