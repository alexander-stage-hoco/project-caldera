using System;

namespace SyntheticSmells.Security
{
    /// <summary>
    /// Missing CSRF protection examples for Roslyn Analyzer testing.
    /// This demonstrates web controllers that lack CSRF protection.
    /// </summary>

    // Simple controller pattern without proper security
    public class InsecureApiController
    {
        // Vulnerable: State-changing operation without CSRF token
        public string CreateUser(string username)
        {
            return $"Created user: {username}";
        }

        // Vulnerable: Update without protection
        public string UpdateUser(int id, string username)
        {
            return $"Updated user {id}: {username}";
        }

        // Vulnerable: Delete without protection
        public string DeleteUser(int id)
        {
            return $"Deleted user: {id}";
        }

        // Vulnerable: Form submission without token validation
        public string SubmitForm(string name, string email)
        {
            return $"Form submitted: {name}";
        }
    }

    // Secure controller example
    public class SecureApiController
    {
        private readonly string _csrfToken = Guid.NewGuid().ToString();

        public bool ValidateCsrfToken(string token)
        {
            return token == _csrfToken;
        }

        // Safe: Validates CSRF token before processing
        public string CreateUserSecure(string username, string csrfToken)
        {
            if (!ValidateCsrfToken(csrfToken))
                throw new UnauthorizedAccessException("Invalid CSRF token");
            return $"Securely created user: {username}";
        }
    }

    public class FormData
    {
        public string Name { get; set; }
        public string Email { get; set; }
    }
}
