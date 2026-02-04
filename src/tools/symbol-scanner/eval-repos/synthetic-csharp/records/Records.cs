namespace Records;

public record Person(string First, string Last);

public record Employee(string First, string Last, string Dept)
{
    public string FullName => $"{First} {Last}";
    public int Years { get; init; }
    public string Display() => $"{FullName} ({Dept})";
}

public readonly record struct Point(int X, int Y)
{
    public double Distance => Math.Sqrt(X * X + Y * Y);
}

public abstract record Animal(string Name);
public record Dog(string Name, string Breed) : Animal(Name);
public record Cat(string Name) : Animal(Name);
