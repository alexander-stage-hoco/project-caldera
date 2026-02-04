// SQL Injection test cases for DevSkim evaluation
// Expected: DevSkim should detect SQL injection vulnerabilities

using System;
using System.Data.SqlClient;

namespace SecurityTests
{
    public class SqlInjection
    {
        private string connectionString = "Server=localhost;Database=test;";

        // VULNERABLE: String concatenation SQL injection (DS126858)
        public void VulnerableQuery1(string userId)
        {
            var cmd = new SqlCommand("SELECT * FROM users WHERE id=" + userId);
            // DevSkim should flag this as SQL injection
        }

        // VULNERABLE: String interpolation SQL injection
        public void VulnerableQuery2(string table, string column)
        {
            string sql = $"SELECT {column} FROM {table}";
            var cmd = new SqlCommand(sql);
            // DevSkim should flag this as SQL injection
        }

        // VULNERABLE: Format string SQL injection
        public void VulnerableQuery3(string searchTerm)
        {
            string query = string.Format("SELECT * FROM products WHERE name LIKE '%{0}%'", searchTerm);
            var cmd = new SqlCommand(query);
            // DevSkim should flag this
        }

        // SAFE: Parameterized query (no finding expected)
        public void SafeQuery(string userId)
        {
            var cmd = new SqlCommand("SELECT * FROM users WHERE id=@id");
            cmd.Parameters.AddWithValue("@id", userId);
            // This should NOT be flagged
        }

        // SAFE: Stored procedure call
        public void SafeStoredProc(string userId)
        {
            var cmd = new SqlCommand("sp_GetUser");
            cmd.CommandType = System.Data.CommandType.StoredProcedure;
            cmd.Parameters.AddWithValue("@userId", userId);
            // This should NOT be flagged
        }
    }
}
