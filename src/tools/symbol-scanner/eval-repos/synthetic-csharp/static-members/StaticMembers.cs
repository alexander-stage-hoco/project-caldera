namespace StaticMembers;

public static class MathConstants
{
    public const double Pi = 3.14159;
    public static readonly double E = 2.71828;
    public static int MaxIterations { get; } = 1000;

    static MathConstants() { }

    public static double Square(double x) => x * x;
    public static double Cube(double x) => Square(x) * x;
}

public class Counter
{
    private static int _count;
    public static int Count => _count;

    public Counter() { _count++; }
    public static void Reset() { _count = 0; }
}
