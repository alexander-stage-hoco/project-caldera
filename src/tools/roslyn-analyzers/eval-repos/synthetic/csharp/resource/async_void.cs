using System;
using System.Threading.Tasks;

namespace SyntheticSmells.Resource
{
    /// <summary>
    /// Async void method examples for Roslyn Analyzer testing.
    /// Expected violations: CA2007 (custom) / async void detection (4) = 4 total
    /// Note: async void is detected by various analyzers including custom rules
    /// </summary>
    public class AsyncVoidExamples
    {
        // async void - cannot be awaited, exceptions lost (line 15)
        public async void FireAndForget1()
        {
            await Task.Delay(100);
            // Any exception here will crash the process!
            throw new InvalidOperationException("Oops");
        }

        // async void - incorrect event handler pattern (line 23)
        public async void ProcessDataAsync(object data)
        {
            await Task.Delay(50);
            // This looks like it should be awaitable but isn't
        }

        // async void - service method (line 31)
        public async void StartBackgroundWork()
        {
            while (true)
            {
                await Task.Delay(1000);
                DoWork();
            }
        }

        // async void - initialization (line 41)
        public async void Initialize()
        {
            await LoadConfigurationAsync();
            await SetupServicesAsync();
            // Caller cannot wait for this to complete!
        }

        private void DoWork() { }
        private Task LoadConfigurationAsync() => Task.CompletedTask;
        private Task SetupServicesAsync() => Task.CompletedTask;

        // OK: async void for event handlers (this is the only valid use)
        public async void Button_Click(object sender, EventArgs e)
        {
            await Task.Delay(100);
            // This is acceptable for UI event handlers
        }

        // OK: Proper async Task method (no violation)
        public async Task ProcessDataProperAsync(object data)
        {
            await Task.Delay(50);
        }

        // OK: Proper async Task for background work (no violation)
        public async Task StartBackgroundWorkProperAsync()
        {
            while (true)
            {
                await Task.Delay(1000);
                DoWork();
            }
        }

        // OK: Proper async Task<T> method (no violation)
        public async Task<string> GetDataAsync()
        {
            await Task.Delay(100);
            return "data";
        }
    }
}
