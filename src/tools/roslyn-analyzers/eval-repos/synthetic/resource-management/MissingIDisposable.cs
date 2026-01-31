using System;
using System.IO;
using System.Net.Http;

namespace ResourceManagement.IDisposable
{
    /// <summary>
    /// Types that should implement IDisposable but don't.
    /// Expected violations: CA1001 (Types that own disposable fields should be disposable)
    /// </summary>

    // CA1001: Type owns disposable field but doesn't implement IDisposable
    public class FileHandler
    {
        private readonly FileStream _stream;  // Disposable field

        public FileHandler(string path)
        {
            _stream = new FileStream(path, FileMode.OpenOrCreate);
        }

        public void Write(string content)
        {
            using var writer = new StreamWriter(_stream, leaveOpen: true);
            writer.Write(content);
        }
        // Missing IDisposable implementation
    }

    // CA1001: Multiple disposable fields
    public class ResourceHolder
    {
        private readonly Stream _input;
        private readonly Stream _output;
        private readonly HttpClient _client;

        public ResourceHolder()
        {
            _input = new MemoryStream();
            _output = new MemoryStream();
            _client = new HttpClient();
        }

        public void Process()
        {
            // Do something with resources
        }
        // Missing IDisposable implementation
    }

    // CA1001: Disposable field assigned in method
    public class LazyResourceHolder
    {
        private FileStream? _file;

        public void Open(string path)
        {
            _file = new FileStream(path, FileMode.Open);
        }

        public void Read()
        {
            if (_file != null)
            {
                var buffer = new byte[100];
                _file.Read(buffer, 0, 100);
            }
        }
        // Missing IDisposable - _file is never disposed
    }

    // CA1001: Disposable through property
    public class ConnectionManager
    {
        public HttpClient Client { get; } = new HttpClient();

        public void Fetch(string url)
        {
            var result = Client.GetStringAsync(url).Result;
            Console.WriteLine(result);
        }
        // Missing IDisposable
    }

    /// <summary>
    /// Clean IDisposable implementation
    /// </summary>
    public class SafeResourceHolder : IDisposable
    {
        private readonly Stream _stream;
        private bool _disposed;

        public SafeResourceHolder()
        {
            _stream = new MemoryStream();
        }

        public void DoWork()
        {
            ObjectDisposedException.ThrowIf(_disposed, this);
            // Work with _stream
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
                    _stream.Dispose();
                }
                _disposed = true;
            }
        }
    }
}
