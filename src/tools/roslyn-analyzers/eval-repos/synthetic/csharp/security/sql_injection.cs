using System;
using System.Data.SqlClient;

namespace SyntheticSmells.Security
{
    /// <summary>
    /// SQL Injection vulnerability examples for Roslyn Analyzer testing.
    /// Expected violations: CA3001 (3), CA2100 (2) = 5 total
    /// Safe patterns: 2
    /// </summary>
    public class SqlInjectionExamples
    {
        // CA3001: SQL Injection - string concatenation (line 15)
        public void VulnerableQuery1(string userId)
        {
            var query = "SELECT * FROM users WHERE id = " + userId;
            using var conn = new SqlConnection("...");
            using var cmd = new SqlCommand(query, conn);
            conn.Open();
            cmd.ExecuteReader();
        }

        // CA3001: SQL Injection - string interpolation (line 28)
        public void VulnerableQuery2(string username)
        {
            using var conn = new SqlConnection("...");
            using var cmd = new SqlCommand($"SELECT * FROM users WHERE name = '{username}'", conn);
            conn.Open();
            cmd.ExecuteReader();
        }

        // CA3001: SQL Injection - Format string (line 39)
        public void VulnerableQuery3(string orderId)
        {
            var query = string.Format("DELETE FROM orders WHERE id = {0}", orderId);
            using var conn = new SqlConnection("...");
            using var cmd = new SqlCommand(query, conn);
            conn.Open();
            cmd.ExecuteNonQuery();
        }

        // CA2100: Review SQL security - CommandText assignment (line 50)
        public void VulnerableCommandText1(string productId)
        {
            using var conn = new SqlConnection("...");
            using var cmd = new SqlCommand();
            cmd.Connection = conn;
            cmd.CommandText = "SELECT * FROM products WHERE id = " + productId;
            conn.Open();
            cmd.ExecuteReader();
        }

        // CA2100: Review SQL security - dynamic query building (line 62)
        public void VulnerableCommandText2(string tableName, string columnValue)
        {
            using var conn = new SqlConnection("...");
            using var cmd = new SqlCommand();
            cmd.Connection = conn;
            cmd.CommandText = "SELECT * FROM " + tableName + " WHERE col = '" + columnValue + "'";
            conn.Open();
            cmd.ExecuteReader();
        }

        // SAFE: Parameterized query (no violation expected)
        public void SafeParameterizedQuery(string userId)
        {
            const string query = "SELECT * FROM users WHERE id = @userId";
            using var conn = new SqlConnection("...");
            using var cmd = new SqlCommand(query, conn);
            cmd.Parameters.AddWithValue("@userId", userId);
            conn.Open();
            cmd.ExecuteReader();
        }

        // SAFE: Stored procedure (no violation expected)
        public void SafeStoredProcedure(string userId)
        {
            using var conn = new SqlConnection("...");
            using var cmd = new SqlCommand("sp_GetUserById", conn);
            cmd.CommandType = System.Data.CommandType.StoredProcedure;
            cmd.Parameters.AddWithValue("@userId", userId);
            conn.Open();
            cmd.ExecuteReader();
        }
    }
}
