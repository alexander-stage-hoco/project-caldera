using System;
using Microsoft.AspNetCore.Mvc;

namespace SyntheticSmells.Security
{
    /// <summary>
    /// ASP.NET Core CSRF vulnerability examples for CA3147 detection.
    /// These patterns represent state-changing actions without CSRF protection.
    /// </summary>
    public class CsrfController : Controller
    {
        // Vulnerable: POST without [ValidateAntiForgeryToken] (CA3147)
        [HttpPost]
        public IActionResult CreateUser(string name, string email)
        {
            // State-changing operation without CSRF protection
            return Ok($"Created user: {name}");
        }

        // Vulnerable: PUT without CSRF protection (CA3147)
        [HttpPut]
        public IActionResult UpdateUser(int id, string name)
        {
            // State-changing operation without CSRF protection
            return Ok($"Updated user {id}: {name}");
        }

        // Vulnerable: DELETE without CSRF protection (CA3147)
        [HttpDelete]
        public IActionResult DeleteUser(int id)
        {
            // State-changing operation without CSRF protection
            return Ok($"Deleted user: {id}");
        }

        // Vulnerable: PATCH without CSRF protection (CA3147)
        [HttpPatch]
        public IActionResult PatchUser(int id, string field, string value)
        {
            // State-changing operation without CSRF protection
            return Ok($"Patched user {id}: {field}={value}");
        }

        // SAFE: Has [ValidateAntiForgeryToken] attribute
        [HttpPost]
        [ValidateAntiForgeryToken]
        public IActionResult SecureCreateUser(string name, string email)
        {
            // Protected with CSRF token validation
            return Ok($"Securely created user: {name}");
        }

        // SAFE: GET request (no CSRF needed)
        [HttpGet]
        public IActionResult GetUser(int id)
        {
            // Read-only operation doesn't need CSRF protection
            return Ok($"User {id}");
        }

        // SAFE: API controller with [ApiController] typically uses different auth
        // Note: In real scenarios, [IgnoreAntiforgeryToken] might be used for APIs
    }

    // Another vulnerable controller pattern
    public class FormController : Controller
    {
        // Vulnerable: Form submission without CSRF token (CA3147)
        [HttpPost]
        public IActionResult SubmitForm(string name, string message)
        {
            return Ok($"Form submitted by {name}");
        }

        // Vulnerable: Login without CSRF (CA3147) - common mistake
        [HttpPost]
        public IActionResult Login(string username, string password)
        {
            return Ok("Logged in");
        }
    }
}
