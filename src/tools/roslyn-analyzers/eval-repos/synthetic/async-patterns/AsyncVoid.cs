using System;
using System.Threading.Tasks;

namespace AsyncPatterns.Void
{
    /// <summary>
    /// Async void violations for Roslyn Analyzer testing.
    /// Expected violations: ASYNC0001, VSTHRD100, S3168
    /// Async void methods cannot be awaited and swallow exceptions.
    /// </summary>
    public class AsyncVoidExamples
    {
        // ASYNC0001/VSTHRD100: Avoid async void method
        public async void ProcessDataAsync()
        {
            await Task.Delay(100);
            Console.WriteLine("Processing...");
        }

        // ASYNC0001/VSTHRD100: Another async void method
        public async void LoadContentAsync(string url)
        {
            await Task.Delay(100);
            Console.WriteLine($"Loading {url}");
        }

        // ASYNC0001/VSTHRD100: Async void with exception risk
        public async void FetchAndSaveAsync()
        {
            await Task.Delay(100);
            throw new InvalidOperationException("This exception is swallowed!");
        }

        // ASYNC0001: Async void in class method
        public async void InitializeAsync()
        {
            await Task.Delay(50);
            Console.WriteLine("Initialized");
        }

        // OK: Event handler pattern (async void is acceptable)
        public async void OnButtonClick(object sender, EventArgs e)
        {
            await Task.Delay(100);
            Console.WriteLine("Button clicked");
        }

        // OK: Async Task method (correct pattern)
        public async Task ProcessDataAsyncCorrect()
        {
            await Task.Delay(100);
            Console.WriteLine("Processing...");
        }
    }

    public class MoreAsyncVoidIssues
    {
        // ASYNC0001: Fire and forget pattern
        public async void FireAndForget()
        {
            await Task.Run(() =>
            {
                // Long running operation
                Task.Delay(1000).Wait();
            });
        }

        // ASYNC0001: Lambda async void
        public void RegisterCallbacks()
        {
            Action callback = async () =>
            {
                // ASYNC0001: Async void lambda
                await Task.Delay(100);
            };
            callback();
        }

        // OK: Async Task
        public async Task CorrectPattern()
        {
            await Task.Delay(100);
        }
    }
}
