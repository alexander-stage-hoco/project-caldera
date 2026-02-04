using System;

namespace EventsDelegates;

/// <summary>
/// Custom delegate for data processing.
/// </summary>
public delegate void DataHandler(string data);

/// <summary>
/// Custom delegate with return value.
/// </summary>
public delegate int Calculator(int a, int b);

/// <summary>
/// Event arguments for data events.
/// </summary>
public class DataEventArgs : EventArgs
{
    public string Data { get; }
    public DateTime Timestamp { get; }

    public DataEventArgs(string data)
    {
        Data = data;
        Timestamp = DateTime.UtcNow;
    }
}

/// <summary>
/// Publisher class that raises events.
/// </summary>
public class DataPublisher
{
    /// <summary>
    /// Event raised when data is received.
    /// </summary>
    public event EventHandler<DataEventArgs>? DataReceived;

    /// <summary>
    /// Event using custom delegate.
    /// </summary>
    public event DataHandler? DataProcessed;

    /// <summary>
    /// Simple event.
    /// </summary>
    public event EventHandler? Started;

    /// <summary>
    /// Simulates receiving data.
    /// </summary>
    public void ReceiveData(string data)
    {
        OnDataReceived(new DataEventArgs(data));
    }

    /// <summary>
    /// Processes and publishes data.
    /// </summary>
    public void ProcessData(string data)
    {
        DataProcessed?.Invoke(data);
    }

    /// <summary>
    /// Starts the publisher.
    /// </summary>
    public void Start()
    {
        Started?.Invoke(this, EventArgs.Empty);
    }

    protected virtual void OnDataReceived(DataEventArgs e)
    {
        DataReceived?.Invoke(this, e);
    }
}

/// <summary>
/// Subscriber class that handles events.
/// </summary>
public class DataSubscriber
{
    private readonly string _name;

    public DataSubscriber(string name)
    {
        _name = name;
    }

    /// <summary>
    /// Subscribes to a publisher's events.
    /// </summary>
    public void Subscribe(DataPublisher publisher)
    {
        publisher.DataReceived += HandleDataReceived;
        publisher.DataProcessed += HandleDataProcessed;
        publisher.Started += HandleStarted;
    }

    /// <summary>
    /// Unsubscribes from a publisher's events.
    /// </summary>
    public void Unsubscribe(DataPublisher publisher)
    {
        publisher.DataReceived -= HandleDataReceived;
        publisher.DataProcessed -= HandleDataProcessed;
        publisher.Started -= HandleStarted;
    }

    private void HandleDataReceived(object? sender, DataEventArgs e)
    {
        Console.WriteLine($"[{_name}] Received: {e.Data} at {e.Timestamp}");
    }

    private void HandleDataProcessed(string data)
    {
        Console.WriteLine($"[{_name}] Processed: {data}");
    }

    private void HandleStarted(object? sender, EventArgs e)
    {
        Console.WriteLine($"[{_name}] Publisher started");
    }
}

/// <summary>
/// Demonstrates delegate usage.
/// </summary>
public class DelegateExamples
{
    /// <summary>
    /// Uses built-in delegates.
    /// </summary>
    public void UseBuiltInDelegates()
    {
        // Action delegate (no return value)
        Action<string> logger = message => Console.WriteLine(message);
        logger("Hello");

        // Func delegate (with return value)
        Func<int, int, int> adder = (a, b) => a + b;
        int sum = adder(3, 4);

        // Predicate delegate (returns bool)
        Predicate<int> isPositive = n => n > 0;
        bool result = isPositive(5);
    }

    /// <summary>
    /// Uses custom delegates.
    /// </summary>
    public void UseCustomDelegates()
    {
        Calculator add = (a, b) => a + b;
        Calculator multiply = (a, b) => a * b;

        int sum = add(5, 3);
        int product = multiply(5, 3);

        // Multicast delegate
        DataHandler handler = data => Console.WriteLine($"Handler 1: {data}");
        handler += data => Console.WriteLine($"Handler 2: {data}");
        handler("test");
    }
}
