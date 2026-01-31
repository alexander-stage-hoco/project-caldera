using System;

namespace SyntheticSmells.DeadCode
{
    /// <summary>
    /// Unused parameter examples for Roslyn Analyzer testing.
    /// Expected violations: IDE0060/CA1801 (5) = 5 total
    /// </summary>
    public class UnusedParametersExamples
    {
        // IDE0060: Parameter 'options' is never used (line 13)
        public void ProcessData(string data, object options)
        {
            Console.WriteLine(data);
            // options is never used!
        }

        // IDE0060: Parameter 'logger' is never used (line 21)
        public int Calculate(int a, int b, ILogger logger)
        {
            return a + b;
            // logger is never used!
        }

        // IDE0060: Parameters 'timeout' and 'retries' are never used (line 29)
        public string FetchResource(string url, int timeout, int retries)
        {
            return $"Content from {url}";
            // timeout and retries are never used!
        }

        // IDE0060: Parameter 'context' is never used (line 37)
        public void HandleEvent(string eventName, EventContext context)
        {
            Console.WriteLine($"Event: {eventName}");
            // context is never used!
        }

        // OK: All parameters used (no violation)
        public void ProcessWithAllUsed(string data, object options, ILogger logger)
        {
            logger.Log($"Processing: {data} with options: {options}");
        }

        // OK: Parameter used in method body (no violation)
        public int Add(int a, int b)
        {
            return a + b;
        }

        // OK: Virtual method - parameters may be used by overrides
        public virtual void VirtualMethod(string unused)
        {
            // Base implementation doesn't use the parameter
            // but overrides might
        }

        // OK: Interface implementation - parameters required by contract
        public void InterfaceMethod(string required)
        {
            // May not use parameter but required by interface
        }
    }

    public interface ILogger
    {
        void Log(string message);
    }

    public class EventContext
    {
        public string Source { get; set; }
    }
}
