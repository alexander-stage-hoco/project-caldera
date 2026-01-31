using System;
using System.Threading.Tasks;

namespace AsyncPatterns.ConfigureAwait
{
    /// <summary>
    /// Missing ConfigureAwait violations for library code.
    /// Expected violations: CA2007 (Consider calling ConfigureAwait)
    /// </summary>
    public class MissingConfigureAwait
    {
        // CA2007: Missing ConfigureAwait in library code
        public async Task ProcessDataAsync()
        {
            await Task.Delay(100);  // CA2007
            Console.WriteLine("Done");
        }

        // CA2007: Multiple await without ConfigureAwait
        public async Task<int> ComputeAsync()
        {
            await Task.Delay(50);   // CA2007
            int result = 42;
            await Task.Delay(50);   // CA2007
            return result;
        }

        // CA2007: Chained awaits
        public async Task<string> FetchAndProcessAsync()
        {
            var data = await GetDataAsync();    // CA2007
            var processed = await ProcessAsync(data);  // CA2007
            return processed;
        }

        private async Task<string> GetDataAsync()
        {
            await Task.Delay(100);  // CA2007
            return "data";
        }

        private async Task<string> ProcessAsync(string input)
        {
            await Task.Delay(100);  // CA2007
            return input.ToUpper();
        }

        // CA2007: In conditional
        public async Task ConditionalAwait(bool condition)
        {
            if (condition)
            {
                await Task.Delay(100);  // CA2007
            }
            else
            {
                await Task.Delay(200);  // CA2007
            }
        }
    }

    /// <summary>
    /// Clean ConfigureAwait patterns for library code
    /// </summary>
    public class SafeConfigureAwaitExamples
    {
        // OK: Using ConfigureAwait(false) in library code
        public async Task ProcessDataAsync()
        {
            await Task.Delay(100).ConfigureAwait(false);
            Console.WriteLine("Done");
        }

        // OK: Multiple awaits with ConfigureAwait
        public async Task<int> ComputeAsync()
        {
            await Task.Delay(50).ConfigureAwait(false);
            int result = 42;
            await Task.Delay(50).ConfigureAwait(false);
            return result;
        }

        // OK: Properly configured
        public async Task<string> FetchAndProcessAsync()
        {
            var data = await GetDataAsync().ConfigureAwait(false);
            var processed = await ProcessAsync(data).ConfigureAwait(false);
            return processed;
        }

        private async Task<string> GetDataAsync()
        {
            await Task.Delay(100).ConfigureAwait(false);
            return "data";
        }

        private async Task<string> ProcessAsync(string input)
        {
            await Task.Delay(100).ConfigureAwait(false);
            return input.ToUpper();
        }
    }
}
