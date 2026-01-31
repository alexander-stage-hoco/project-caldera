using System;
using System.IO;

namespace SyntheticSmells.Resource
{
    /// <summary>
    /// Improper IDisposable implementation examples for Roslyn Analyzer testing.
    /// Expected violations: CA1063 (3) = 3 total
    /// </summary>

    // CA1063: Dispose method should call base.Dispose (line 13)
    public class ImproperDispose1 : DisposableBase
    {
        private readonly FileStream _stream;

        public ImproperDispose1(string path) : base()
        {
            _stream = new FileStream(path, FileMode.OpenOrCreate);
        }

        // Missing call to base.Dispose(disposing)!
        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                _stream?.Dispose();
            }
            // Should call: base.Dispose(disposing);
        }
    }

    // CA1063: Dispose pattern implemented incorrectly (line 33)
    public class ImproperDispose2 : IDisposable
    {
        private readonly MemoryStream _buffer;
        private bool _disposed;

        public ImproperDispose2()
        {
            _buffer = new MemoryStream();
        }

        // Wrong: Dispose should be non-virtual
        public virtual void Dispose()
        {
            _buffer?.Dispose();
            _disposed = true;
        }

        // Missing: protected virtual Dispose(bool disposing)
        // Missing: GC.SuppressFinalize(this)
    }

    // CA1063: IDisposable.Dispose should not be virtual (line 56)
    public class ImproperDispose3 : IDisposable
    {
        private IntPtr _handle;

        public ImproperDispose3()
        {
            _handle = IntPtr.Zero;
        }

        // Virtual Dispose is wrong - should be protected virtual Dispose(bool)
        public virtual void Dispose()
        {
            if (_handle != IntPtr.Zero)
            {
                // Release handle
                _handle = IntPtr.Zero;
            }
        }
    }

    // Base class for testing
    public class DisposableBase : IDisposable
    {
        private bool _disposed;

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed)
            {
                _disposed = true;
            }
        }
    }

    // OK: Properly implemented IDisposable pattern (no violation)
    public class ProperDisposePattern : IDisposable
    {
        private readonly FileStream _stream;
        private bool _disposed;

        public ProperDisposePattern(string path)
        {
            _stream = new FileStream(path, FileMode.OpenOrCreate);
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed)
            {
                if (disposing)
                {
                    _stream?.Dispose();
                }
                _disposed = true;
            }
        }

        ~ProperDisposePattern()
        {
            Dispose(false);
        }
    }
}
