using System;

namespace NullSafety.Uninitialized
{
    /// <summary>
    /// Uninitialized non-nullable member violations.
    /// Expected violations: CS8618 (Non-nullable field/property must contain a non-null value)
    /// </summary>
    public class UserProfile
    {
        // CS8618: Non-nullable field 'Name' must contain a non-null value
        public string Name;

        // CS8618: Non-nullable property 'Email' must contain a non-null value
        public string Email { get; set; }

        // CS8618: Non-nullable property uninitialized in constructor path
        public string Address { get; set; }

        // OK: Nullable - doesn't require initialization
        public string? NickName { get; set; }

        // OK: Initialized in declaration
        public string Country { get; set; } = "Unknown";

        public UserProfile()
        {
            // Name, Email, and Address are not initialized
        }
    }

    public class DatabaseConnection
    {
        // CS8618: Multiple uninitialized fields
        public string ConnectionString;
        public string Database;
        public string Server;

        // OK: Nullable
        public string? Schema;

        // OK: Initialized
        public int Port = 5432;
    }

    public class Configuration
    {
        // CS8618: Uninitialized non-nullable property
        public string ApiKey { get; set; }

        // CS8618: Another uninitialized property
        public string SecretKey { get; set; }

        // Constructor doesn't initialize all non-nullable members
        public Configuration(string apiKey)
        {
            ApiKey = apiKey;
            // SecretKey is not initialized
        }
    }

    /// <summary>
    /// Clean example with proper initialization
    /// </summary>
    public class CleanProfile
    {
        public string Name { get; set; }
        public string Email { get; set; }
        public string? Optional { get; set; }

        public CleanProfile(string name, string email)
        {
            Name = name;
            Email = email;
        }
    }
}
