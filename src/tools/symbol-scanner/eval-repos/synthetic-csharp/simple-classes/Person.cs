using System;

namespace SimpleClasses;

/// <summary>
/// Represents a person with basic properties.
/// </summary>
public class Person
{
    private string _name;
    private int _age;

    /// <summary>
    /// Gets or sets the person's name.
    /// </summary>
    public string Name
    {
        get => _name;
        set => _name = value ?? throw new ArgumentNullException(nameof(value));
    }

    /// <summary>
    /// Gets or sets the person's age.
    /// </summary>
    public int Age
    {
        get => _age;
        set => _age = value >= 0 ? value : throw new ArgumentOutOfRangeException(nameof(value));
    }

    /// <summary>
    /// Creates a new person.
    /// </summary>
    public Person(string name, int age)
    {
        Name = name;
        Age = age;
    }

    /// <summary>
    /// Returns a greeting message.
    /// </summary>
    public string Greet()
    {
        return $"Hello, my name is {Name} and I am {Age} years old.";
    }

    /// <summary>
    /// Checks if the person is an adult.
    /// </summary>
    public bool IsAdult()
    {
        return Age >= 18;
    }
}

/// <summary>
/// Simple struct for coordinates.
/// </summary>
public struct Point
{
    public int X { get; set; }
    public int Y { get; set; }

    public Point(int x, int y)
    {
        X = x;
        Y = y;
    }

    public double DistanceFromOrigin()
    {
        return Math.Sqrt(X * X + Y * Y);
    }
}
