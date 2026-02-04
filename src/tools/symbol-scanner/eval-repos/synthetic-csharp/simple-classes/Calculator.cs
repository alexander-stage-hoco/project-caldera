namespace SimpleClasses;

/// <summary>
/// Basic calculator class.
/// </summary>
public class Calculator
{
    /// <summary>
    /// Adds two numbers.
    /// </summary>
    public int Add(int a, int b)
    {
        return a + b;
    }

    /// <summary>
    /// Subtracts b from a.
    /// </summary>
    public int Subtract(int a, int b)
    {
        return a - b;
    }

    /// <summary>
    /// Multiplies two numbers.
    /// </summary>
    public int Multiply(int a, int b)
    {
        return a * b;
    }

    /// <summary>
    /// Divides a by b.
    /// </summary>
    public double Divide(int a, int b)
    {
        if (b == 0)
        {
            throw new System.DivideByZeroException("Cannot divide by zero");
        }
        return (double)a / b;
    }
}

/// <summary>
/// Static utility class.
/// </summary>
public static class MathUtils
{
    /// <summary>
    /// Computes factorial.
    /// </summary>
    public static long Factorial(int n)
    {
        if (n < 0) throw new System.ArgumentException("n must be non-negative");
        if (n <= 1) return 1;
        return n * Factorial(n - 1);
    }

    /// <summary>
    /// Checks if a number is prime.
    /// </summary>
    public static bool IsPrime(int n)
    {
        if (n < 2) return false;
        for (int i = 2; i * i <= n; i++)
        {
            if (n % i == 0) return false;
        }
        return true;
    }
}
