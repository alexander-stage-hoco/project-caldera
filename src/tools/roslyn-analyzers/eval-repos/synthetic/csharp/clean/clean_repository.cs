using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.Threading;
using System.Threading.Tasks;

namespace SyntheticSmells.Clean
{
    /// <summary>
    /// Clean repository implementation with proper IDisposable.
    /// Expected violations: 0
    /// Demonstrates correct dispose pattern and parameterized queries.
    /// </summary>
    public sealed class CleanRepository : IDisposable
    {
        private readonly string _connectionString;
        private SqlConnection _connection;
        private bool _disposed;

        public CleanRepository(string connectionString)
        {
            _connectionString = connectionString ?? throw new ArgumentNullException(nameof(connectionString));
        }

        public Task<IReadOnlyList<DataRecord>> GetAllAsync(CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();

            var records = new List<DataRecord>();

            using var connection = new SqlConnection(_connectionString);
            connection.Open();

            const string query = "SELECT Id, Name, Value, CreatedAt FROM Records ORDER BY CreatedAt DESC";
            using var command = new SqlCommand(query, connection);

            using var reader = command.ExecuteReader();
            while (reader.Read())
            {
                records.Add(new DataRecord
                {
                    Id = reader.GetInt32(0),
                    Name = reader.GetString(1),
                    Value = reader.GetDecimal(2),
                    CreatedAt = reader.GetDateTime(3)
                });
            }

            return Task.FromResult<IReadOnlyList<DataRecord>>(records);
        }

        public Task<DataRecord> GetByIdAsync(int id, CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();

            using var connection = new SqlConnection(_connectionString);
            connection.Open();

            // Safe: Parameterized query prevents SQL injection
            const string query = "SELECT Id, Name, Value, CreatedAt FROM Records WHERE Id = @Id";
            using var command = new SqlCommand(query, connection);
            command.Parameters.AddWithValue("@Id", id);

            using var reader = command.ExecuteReader();
            if (reader.Read())
            {
                return Task.FromResult(new DataRecord
                {
                    Id = reader.GetInt32(0),
                    Name = reader.GetString(1),
                    Value = reader.GetDecimal(2),
                    CreatedAt = reader.GetDateTime(3)
                });
            }

            return Task.FromResult<DataRecord>(null);
        }

        public Task InsertAsync(DataRecord record, CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();

            if (record == null)
                throw new ArgumentNullException(nameof(record));

            using var connection = new SqlConnection(_connectionString);
            connection.Open();

            // Safe: Parameterized query
            const string query = "INSERT INTO Records (Name, Value, CreatedAt) VALUES (@Name, @Value, @CreatedAt)";
            using var command = new SqlCommand(query, connection);
            command.Parameters.AddWithValue("@Name", record.Name);
            command.Parameters.AddWithValue("@Value", record.Value);
            command.Parameters.AddWithValue("@CreatedAt", record.CreatedAt);

            command.ExecuteNonQuery();
            return Task.CompletedTask;
        }

        private void ThrowIfDisposed()
        {
            if (_disposed)
                throw new ObjectDisposedException(nameof(CleanRepository));
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                _connection?.Dispose();
                _disposed = true;
            }
        }
    }

    public class DataRecord
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public decimal Value { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}
