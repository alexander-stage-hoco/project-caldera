// Test file for C4, H5: Service Locator and Hidden Dependencies
// Expected detections: 5 (C4 x3, H5 x2)

using System;

namespace Synthetic.CSharp
{
    public interface ILogger
    {
        void Log(string message);
    }

    public interface IService
    {
        void Execute();
    }

    public class ConsoleLogger : ILogger
    {
        public void Log(string message) => Console.WriteLine(message);
    }

    public class EmailService : IService
    {
        public void Execute() => Console.WriteLine("Sending email");
    }

    // Mock service locator for testing
    public static class ServiceLocator
    {
        public static T GetService<T>() => default;
        public static T Resolve<T>() => default;
        public static IServiceProvider Current { get; }
    }

    public static class ServiceLocatorCurrent
    {
        public static T GetInstance<T>() => default;
    }

    public interface IServiceProvider
    {
        T GetRequiredService<T>();
    }

    public class BadServiceConsumer
    {
        private readonly ILogger _logger;

        // H5: Hidden dependency - creating service in constructor
        public BadServiceConsumer()
        {
            _logger = new ConsoleLogger();  // Expected: DD-H5-HIDDEN-DEPENDENCY-csharp
        }

        // C4: Service Locator anti-pattern
        public void DoWork()
        {
            var service = ServiceLocator.GetService<IService>();  // Expected: DD-C4-SERVICE-LOCATOR-csharp-getservice
            service?.Execute();
        }

        // C4: Service Locator anti-pattern (Resolve)
        public void DoMoreWork()
        {
            var service = ServiceLocator.Resolve<IService>();  // Expected: DD-C4-SERVICE-LOCATOR-csharp-resolve
            service?.Execute();
        }

        // C4: Service Locator anti-pattern (GetRequiredService)
        public void DoEvenMoreWork(IServiceProvider provider)
        {
            var service = provider.GetRequiredService<IService>();  // Expected: DD-C4-SERVICE-LOCATOR-csharp-getrequired
            service?.Execute();
        }
    }

    public class AnotherBadService
    {
        private readonly IService _service;

        // H5: Hidden dependency
        public AnotherBadService(string config)
        {
            _service = new EmailService();  // Expected: DD-H5-HIDDEN-DEPENDENCY-csharp
            Console.WriteLine(config);
        }
    }

    // GOOD: Proper dependency injection
    public class GoodServiceConsumer
    {
        private readonly ILogger _logger;
        private readonly IService _service;

        public GoodServiceConsumer(ILogger logger, IService service)
        {
            _logger = logger;    // No detection - injected
            _service = service;  // No detection - injected
        }
    }
}
