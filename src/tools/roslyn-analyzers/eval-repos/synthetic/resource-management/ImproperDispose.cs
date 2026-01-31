using System;
using System.IO;

namespace ResourceManagement.ImproperDispose
{
    /// <summary>
    /// Improper IDisposable implementation violations.
    /// Expected violations: CA1063, CA1816, IDISP006
    /// </summary>

    // CA1063: Implement IDisposable correctly
    public class IncompleteDisposable : IDisposable
    {
        private readonly Stream _stream;

        public IncompleteDisposable()
        {
            _stream = new MemoryStream();
        }

        // CA1063: Dispose() doesn't call Dispose(true)
        public void Dispose()
        {
            _stream.Dispose();
            // Missing: Dispose(true)
            // Missing: GC.SuppressFinalize(this)
        }
    }

    // CA1063: Unsealed type with finalizer
    public class FinalizerWithoutVirtualDispose : IDisposable
    {
        private readonly IntPtr _handle;

        public FinalizerWithoutVirtualDispose()
        {
            _handle = IntPtr.Zero;
        }

        ~FinalizerWithoutVirtualDispose()
        {
            // CA1063: Finalizer should call Dispose(false)
            Dispose();  // Wrong: calls Dispose() not Dispose(false)
        }

        public void Dispose()
        {
            // Missing virtual Dispose(bool) pattern
        }
    }

    // CA1816: Dispose should call SuppressFinalize
    public class MissingSuppressFinalize : IDisposable
    {
        private readonly Stream _stream = new MemoryStream();
        private bool _disposed;

        public void Dispose()
        {
            Dispose(true);
            // CA1816: Missing GC.SuppressFinalize(this)
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed)
            {
                if (disposing)
                {
                    _stream.Dispose();
                }
                _disposed = true;
            }
        }
    }

    // IDISP006: Dispose member in virtual dispose method
    public class WrongDisposeLocation : IDisposable
    {
        private readonly Stream _stream = new MemoryStream();
        private bool _disposed;

        // IDISP006: Should dispose _stream in Dispose(bool), not here
        public void Dispose()
        {
            if (!_disposed)
            {
                _stream.Dispose();  // Wrong location
                _disposed = true;
            }
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            // Dispose logic should be here
        }
    }

    /// <summary>
    /// Correct IDisposable implementation
    /// </summary>
    public class CorrectDisposable : IDisposable
    {
        private readonly Stream _stream = new MemoryStream();
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
                if (disposing)
                {
                    _stream.Dispose();
                }
                _disposed = true;
            }
        }

        ~CorrectDisposable()
        {
            Dispose(false);
        }
    }
}
