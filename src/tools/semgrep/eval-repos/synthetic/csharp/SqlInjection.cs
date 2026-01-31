/**
 * Test file for SQL Injection vulnerability detection.
 * Contains multiple SQL injection patterns for C#.
 */

using System;
using System.Data;
using System.Data.SqlClient;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;

namespace SmellTests.Security
{
    public class SqlInjectionExamples
    {
        private readonly string _connectionString = "Server=localhost;Database=test;";

        // SQL_INJECTION: String concatenation in SQL query
        public DataTable GetUserByName(string userName)
        {
            using var connection = new SqlConnection(_connectionString);
            // BAD: Direct string concatenation
            string query = "SELECT * FROM Users WHERE Name = '" + userName + "'";
            using var command = new SqlCommand(query, connection);
            var adapter = new SqlDataAdapter(command);
            var table = new DataTable();
            adapter.Fill(table);
            return table;
        }

        // SQL_INJECTION: String interpolation in SQL query
        public async Task<int> DeleteUser(int userId, string reason)
        {
            using var connection = new SqlConnection(_connectionString);
            // BAD: String interpolation
            string query = $"DELETE FROM Users WHERE Id = {userId} AND Reason LIKE '%{reason}%'";
            using var command = new SqlCommand(query, connection);
            await connection.OpenAsync();
            return await command.ExecuteNonQueryAsync();
        }

        // SQL_INJECTION: String.Format in SQL query
        public DataTable SearchProducts(string searchTerm, string category)
        {
            using var connection = new SqlConnection(_connectionString);
            // BAD: String.Format
            string query = string.Format(
                "SELECT * FROM Products WHERE Name LIKE '%{0}%' AND Category = '{1}'",
                searchTerm,
                category);
            using var command = new SqlCommand(query, connection);
            var adapter = new SqlDataAdapter(command);
            var table = new DataTable();
            adapter.Fill(table);
            return table;
        }

        // SQL_INJECTION: ExecuteSqlRaw with string concatenation
        public void UpdateOrderStatus(DbContext context, int orderId, string status)
        {
            // BAD: Raw SQL with concatenation in EF Core
            context.Database.ExecuteSqlRaw(
                "UPDATE Orders SET Status = '" + status + "' WHERE Id = " + orderId);
        }

        // SQL_INJECTION: Dynamic ORDER BY clause
        public DataTable GetSortedUsers(string sortColumn)
        {
            using var connection = new SqlConnection(_connectionString);
            // BAD: Dynamic column name (still injectable)
            string query = "SELECT * FROM Users ORDER BY " + sortColumn;
            using var command = new SqlCommand(query, connection);
            var adapter = new SqlDataAdapter(command);
            var table = new DataTable();
            adapter.Fill(table);
            return table;
        }

        // SQL_INJECTION: IN clause with user input
        public DataTable GetUsersByIds(string[] userIds)
        {
            using var connection = new SqlConnection(_connectionString);
            // BAD: Building IN clause from user input
            string idList = string.Join(",", userIds);
            string query = "SELECT * FROM Users WHERE Id IN (" + idList + ")";
            using var command = new SqlCommand(query, connection);
            var adapter = new SqlDataAdapter(command);
            var table = new DataTable();
            adapter.Fill(table);
            return table;
        }

        // CORRECT: Parameterized query
        public DataTable GetUserByNameSafe(string userName)
        {
            using var connection = new SqlConnection(_connectionString);
            // GOOD: Using parameters
            string query = "SELECT * FROM Users WHERE Name = @name";
            using var command = new SqlCommand(query, connection);
            command.Parameters.AddWithValue("@name", userName);
            var adapter = new SqlDataAdapter(command);
            var table = new DataTable();
            adapter.Fill(table);
            return table;
        }

        // CORRECT: Using stored procedure
        public DataTable GetUserByIdSafe(int userId)
        {
            using var connection = new SqlConnection(_connectionString);
            using var command = new SqlCommand("sp_GetUserById", connection);
            command.CommandType = CommandType.StoredProcedure;
            command.Parameters.AddWithValue("@userId", userId);
            var adapter = new SqlDataAdapter(command);
            var table = new DataTable();
            adapter.Fill(table);
            return table;
        }
    }
}
