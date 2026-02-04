// Input validation test cases for DevSkim evaluation
// Expected: DevSkim should detect missing input validation patterns

using System;
using System.Text.RegularExpressions;
using System.Web;
using System.IO;

namespace ApiSecurity
{
    public class InputValidation
    {
        // VULNERABLE: No input validation - direct use in file path
        public string ReadUserFile(string filename)
        {
            // Path traversal vulnerability - no validation
            string path = Path.Combine("/app/uploads/", filename);
            return File.ReadAllText(path);
        }

        // VULNERABLE: User input directly in redirect URL
        public void RedirectToUrl(string returnUrl)
        {
            // Open redirect vulnerability
            HttpContext.Current.Response.Redirect(returnUrl);
        }

        // VULNERABLE: Regex from user input (ReDoS risk)
        public bool MatchUserPattern(string input, string userPattern)
        {
            // ReDoS vulnerability - untrusted regex pattern
            var regex = new Regex(userPattern);
            return regex.IsMatch(input);
        }

        // VULNERABLE: User input in process execution
        public void ExecuteCommand(string userInput)
        {
            // Command injection
            System.Diagnostics.Process.Start("cmd.exe", "/c " + userInput);
        }

        // VULNERABLE: Unsafe deserialization of user input
        public object DeserializeUserData(string jsonData)
        {
            // Potential deserialization attack
            var settings = new Newtonsoft.Json.JsonSerializerSettings
            {
                TypeNameHandling = Newtonsoft.Json.TypeNameHandling.All
            };
            return Newtonsoft.Json.JsonConvert.DeserializeObject(jsonData, settings);
        }

        // VULNERABLE: User input in LDAP query
        public void SearchLdap(string username)
        {
            // LDAP injection
            string filter = $"(&(objectClass=user)(sAMAccountName={username}))";
            // DevSkim should flag LDAP injection risk
        }

        // SAFE: Validated input (no finding expected)
        public string ReadValidatedFile(string filename)
        {
            // Proper validation
            if (string.IsNullOrEmpty(filename) ||
                filename.Contains("..") ||
                Path.IsPathRooted(filename))
            {
                throw new ArgumentException("Invalid filename");
            }

            string safePath = Path.Combine("/app/uploads/", Path.GetFileName(filename));
            return File.ReadAllText(safePath);
        }

        // SAFE: Whitelist validation for redirect
        public void SafeRedirect(string returnUrl)
        {
            var allowedUrls = new[] { "/home", "/dashboard", "/profile" };
            if (Array.Exists(allowedUrls, u => u == returnUrl))
            {
                HttpContext.Current.Response.Redirect(returnUrl);
            }
        }

        // SAFE: Parameterized query
        public void SafeQuery(string userInput)
        {
            // Using parameterized queries
            // This should NOT be flagged
        }
    }
}
