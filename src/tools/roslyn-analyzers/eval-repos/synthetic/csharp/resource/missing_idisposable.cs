using System;
using System.IO;
using System.Data.SqlClient;

namespace SyntheticSmells.Resource
{
    /// <summary>
    /// Missing IDisposable implementation examples for Roslyn Analyzer testing.
    /// Expected violations: CA1001 (4) = 4 total
    /// </summary>

    // CA1001: Type owns disposable field but doesn't implement IDisposable (line 13)
    public class MissingDisposable1
    {
        private readonly FileStream _stream;

        public MissingDisposable1(string path)
        {
            _stream = new FileStream(path, FileMode.OpenOrCreate);
        }

        public void Write(byte[] data)
        {
            _stream.Write(data, 0, data.Length);
        }
        // No Dispose method - _stream will leak!
    }

    // CA1001: Type owns multiple disposable fields (line 32)
    public class MissingDisposable2
    {
        private readonly SqlConnection _connection;
        private readonly StreamWriter _writer;

        public MissingDisposable2(string connString, string logPath)
        {
            _connection = new SqlConnection(connString);
            _writer = new StreamWriter(logPath);
        }

        public void Execute(string sql)
        {
            _connection.Open();
            using var cmd = new SqlCommand(sql, _connection);
            cmd.ExecuteNonQuery();
            _writer.WriteLine($"Executed: {sql}");
        }
        // No Dispose method - resources will leak!
    }

    // CA1001: Nested disposable ownership (line 53)
    public class MissingDisposable3
    {
        private readonly MemoryStream _buffer;

        public MissingDisposable3()
        {
            _buffer = new MemoryStream();
        }

        public void AddData(byte[] data)
        {
            _buffer.Write(data, 0, data.Length);
        }

        public byte[] GetData()
        {
            return _buffer.ToArray();
        }
        // No Dispose method!
    }

    // CA1001: Service with disposable resource (line 74)
    public class MissingDisposable4
    {
        private readonly HttpClientWrapper _client;

        public MissingDisposable4()
        {
            _client = new HttpClientWrapper();
        }

        public string Get(string url)
        {
            return _client.GetString(url);
        }
        // No Dispose method!
    }

    // Helper class that is disposable
    public class HttpClientWrapper : IDisposable
    {
        public string GetString(string url) => "";
        public void Dispose() { }
    }

    // OK: Properly implements IDisposable (no violation)
    public class ProperDisposable : IDisposable
    {
        private readonly FileStream _stream;
        private bool _disposed;

        public ProperDisposable(string path)
        {
            _stream = new FileStream(path, FileMode.OpenOrCreate);
        }

        public void Write(byte[] data)
        {
            if (_disposed) throw new ObjectDisposedException(nameof(ProperDisposable));
            _stream.Write(data, 0, data.Length);
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                _stream?.Dispose();
                _disposed = true;
            }
        }
    }
}
