// Test file for E5: Unsafe Lock patterns
// Expected detections: 2 (DD-E5-UNSAFE-LOCK-this, DD-E5-UNSAFE-LOCK-typeof)

using System;
using System.Threading;

namespace Synthetic.CSharp
{
    public class UnsafeLockPatterns
    {
        private int _counter = 0;

        // E5: lock(this) - BAD: can cause deadlocks
        public void IncrementWithLockThis()
        {
            lock (this)  // Expected: DD-E5-UNSAFE-LOCK-this
            {
                _counter++;
            }
        }

        // E5: lock(typeof) - BAD: can cause deadlocks
        public static void StaticOperation()
        {
            lock (typeof(UnsafeLockPatterns))  // Expected: DD-E5-UNSAFE-LOCK-typeof
            {
                Console.WriteLine("Static lock");
            }
        }

        // GOOD: lock on private readonly object
        private readonly object _syncLock = new object();

        public void IncrementSafely()
        {
            lock (_syncLock)  // No detection - this is correct
            {
                _counter++;
            }
        }
    }
}
