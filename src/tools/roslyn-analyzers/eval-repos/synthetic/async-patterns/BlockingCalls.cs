using System;
using System.Threading.Tasks;

namespace AsyncPatterns.Blocking
{
    /// <summary>
    /// Blocking on async code violations.
    /// Expected violations: VSTHRD002, VSTHRD103, VSTHRD110, VSTHRD111
    /// </summary>
    public class BlockingCallExamples
    {
        // VSTHRD002: Avoid synchronously blocking on async code
        public void BlockingResult()
        {
            // Dangerous: Can cause deadlocks
            var result = GetDataAsync().Result;  // VSTHRD002
            Console.WriteLine(result);
        }

        // VSTHRD002: Blocking with Wait()
        public void BlockingWait()
        {
            // Dangerous: Can cause deadlocks
            GetDataAsync().Wait();  // VSTHRD002
        }

        // VSTHRD002: GetAwaiter().GetResult() is slightly better but still blocking
        public string BlockingGetResult()
        {
            // Still blocks the thread
            return GetDataAsync().GetAwaiter().GetResult();  // VSTHRD002
        }

        // VSTHRD103: Call async methods when in async context
        public async Task MixedContext()
        {
            // VSTHRD103: Using sync method when async available
            System.Threading.Thread.Sleep(1000);  // Should use Task.Delay
            await Task.Delay(100);
        }

        // VSTHRD110: Observe result of async call
        public void IgnoreAsyncResult()
        {
            // VSTHRD110: Task result is ignored
            GetDataAsync();  // Warning: Task not awaited or stored
        }

        // VSTHRD111: Use async everywhere
        public string GetDataBlocking()
        {
            // VSTHRD111: Non-async wrapper around async code
            return Task.Run(async () =>
            {
                await Task.Delay(100);
                return "data";
            }).Result;  // Blocking
        }

        private async Task<string> GetDataAsync()
        {
            await Task.Delay(100);
            return "data";
        }
    }

    /// <summary>
    /// More blocking scenarios
    /// </summary>
    public class AdditionalBlockingIssues
    {
        // Blocking in constructor
        public AdditionalBlockingIssues()
        {
            // VSTHRD002: Blocking in constructor
            InitializeAsync().Wait();
        }

        private async Task InitializeAsync()
        {
            await Task.Delay(100);
        }

        // Blocking with timeout
        public void BlockWithTimeout()
        {
            var task = GetDataAsync();
            // VSTHRD002: Blocking with Wait
            if (!task.Wait(TimeSpan.FromSeconds(5)))
            {
                throw new TimeoutException();
            }
        }

        private async Task<string> GetDataAsync()
        {
            await Task.Delay(100);
            return "result";
        }
    }

    /// <summary>
    /// Clean async patterns
    /// </summary>
    public class SafeAsyncPatterns
    {
        // OK: Properly async
        public async Task<string> GetDataAsync()
        {
            await Task.Delay(100);
            return "data";
        }

        // OK: Async all the way
        public async Task ProcessAsync()
        {
            var data = await GetDataAsync();
            Console.WriteLine(data);
        }

        // OK: Fire and forget with proper handling
        public void StartBackgroundWork()
        {
            _ = Task.Run(async () =>
            {
                try
                {
                    await DoWorkAsync();
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Background error: {ex}");
                }
            });
        }

        private async Task DoWorkAsync()
        {
            await Task.Delay(100);
        }
    }
}
