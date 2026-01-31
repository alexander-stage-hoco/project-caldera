/**
 * Test file for BEST_PRACTICE_VIOLATION detection.
 * Tests Thread.Abort, throw ex, GC.Collect, magic strings.
 */

using System;
using System.Threading;
using System.Diagnostics;

namespace SmellTests.BestPractices
{
    public class BestPractices
    {
        // 1. Thread.Abort is dangerous
        public void StopWorker(Thread worker)
        {
            // BEST_PRACTICE: Thread.Abort is deprecated and dangerous
            worker.Abort();
        }

        // 2. Throw ex loses stack trace
        public void HandleError()
        {
            try
            {
                DoWork();
            }
            catch (Exception ex)
            {
                // BEST_PRACTICE: throw ex loses stack trace
                throw ex;
            }
        }

        // 3. GC.Collect() is usually unnecessary
        public void FreeMemory()
        {
            // BEST_PRACTICE: Forcing GC is almost always wrong
            GC.Collect();
        }

        // 4. Magic strings for configuration
        public string GetConnectionString()
        {
            // BEST_PRACTICE: Magic string - should be in config
            return "Server=localhost;Database=mydb;User=admin;Password=secret";
        }

        // 5. Empty catch block
        public void SilentFailure()
        {
            try
            {
                DoWork();
            }
            catch (Exception)
            {
                // BEST_PRACTICE: Empty catch swallows exception
            }
        }

        // 6. Using Debug.Assert in production code
        public void ValidateInput(object input)
        {
            // BEST_PRACTICE: Debug.Assert is removed in release builds
            Debug.Assert(input != null, "Input should not be null");
            Process(input);
        }

        // GOOD: Correct thread cancellation
        private CancellationTokenSource _cts = new CancellationTokenSource();

        public void StopWorkerCorrect()
        {
            _cts.Cancel();
        }

        // GOOD: Preserve stack trace
        public void HandleErrorCorrect()
        {
            try
            {
                DoWork();
            }
            catch (Exception)
            {
                // throw preserves stack trace
                throw;
            }
        }

        // GOOD: Named constant for connection
        private const string ConnectionString = "Server=localhost;Database=mydb";

        public string GetConnectionStringCorrect()
        {
            return ConnectionString;
        }

        // GOOD: Proper validation
        public void ValidateInputCorrect(object input)
        {
            if (input == null)
            {
                throw new ArgumentNullException(nameof(input));
            }
            Process(input);
        }

        private void DoWork() { }
        private void Process(object input) { }
    }
}
