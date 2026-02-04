namespace Inheritance;

/// <summary>
/// Base class for all animals.
/// </summary>
public abstract class Animal
{
    public string Name { get; protected set; }

    protected Animal(string name)
    {
        Name = name;
    }

    /// <summary>
    /// Makes the animal's sound.
    /// </summary>
    public abstract string MakeSound();

    /// <summary>
    /// Moves the animal.
    /// </summary>
    public virtual void Move()
    {
        System.Console.WriteLine($"{Name} is moving");
    }
}

/// <summary>
/// Interface for animals that can fly.
/// </summary>
public interface IFlyable
{
    void Fly();
    int MaxAltitude { get; }
}

/// <summary>
/// Interface for animals that can swim.
/// </summary>
public interface ISwimmable
{
    void Swim();
    int MaxDepth { get; }
}

/// <summary>
/// A dog that barks.
/// </summary>
public class Dog : Animal
{
    public string Breed { get; }

    public Dog(string name, string breed) : base(name)
    {
        Breed = breed;
    }

    public override string MakeSound()
    {
        return "Woof!";
    }

    public void Fetch()
    {
        System.Console.WriteLine($"{Name} is fetching the ball");
    }
}

/// <summary>
/// A bird that can fly.
/// </summary>
public class Bird : Animal, IFlyable
{
    public int MaxAltitude { get; }

    public Bird(string name, int maxAltitude) : base(name)
    {
        MaxAltitude = maxAltitude;
    }

    public override string MakeSound()
    {
        return "Tweet!";
    }

    public void Fly()
    {
        System.Console.WriteLine($"{Name} is flying at {MaxAltitude}m");
    }

    public override void Move()
    {
        Fly();
    }
}

/// <summary>
/// A duck that can fly and swim.
/// </summary>
public class Duck : Animal, IFlyable, ISwimmable
{
    public int MaxAltitude { get; }
    public int MaxDepth { get; }

    public Duck(string name) : base(name)
    {
        MaxAltitude = 1000;
        MaxDepth = 5;
    }

    public override string MakeSound()
    {
        return "Quack!";
    }

    public void Fly()
    {
        System.Console.WriteLine($"{Name} is flying");
    }

    public void Swim()
    {
        System.Console.WriteLine($"{Name} is swimming");
    }
}
