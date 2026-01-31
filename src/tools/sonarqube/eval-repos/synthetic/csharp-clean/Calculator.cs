namespace CleanCode;

/// <summary>
/// A simple calculator with basic operations.
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
    /// <exception cref="DivideByZeroException">Thrown when b is zero.</exception>
    public double Divide(double a, double b)
    {
        if (b == 0)
        {
            throw new DivideByZeroException("Cannot divide by zero");
        }
        return a / b;
    }
}
