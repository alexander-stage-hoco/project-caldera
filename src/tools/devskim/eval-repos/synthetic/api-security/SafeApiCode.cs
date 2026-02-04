// Safe API code patterns for DevSkim evaluation
// Expected: No security issues should be detected

using System;
using System.Web.Http;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;

namespace ApiSecurity
{
    /// <summary>
    /// This class demonstrates secure API coding patterns.
    /// DevSkim should NOT flag any of these as security issues.
    /// </summary>
    [Authorize]
    public class SafeApiController : ApiController
    {
        // SAFE: Proper HTTPS configuration
        private readonly Uri _baseUri = new Uri("https://secure-api.example.com");

        // SAFE: Using configuration for secrets
        private string GetApiKey()
        {
            return Environment.GetEnvironmentVariable("SECURE_API_KEY")
                ?? throw new InvalidOperationException("API key not configured");
        }

        // SAFE: Proper input validation
        [HttpGet]
        [Route("api/secure/items/{id}")]
        public IHttpActionResult GetItem(int id)
        {
            if (id <= 0)
            {
                return BadRequest("Invalid ID");
            }

            // Parameterized database query would go here
            return Ok(new { Id = id, Name = "Secure Item" });
        }

        // SAFE: Proper error handling without info disclosure
        [HttpPost]
        [Route("api/secure/process")]
        public IHttpActionResult ProcessData([FromBody] DataRequest request)
        {
            try
            {
                if (request == null)
                {
                    return BadRequest();
                }

                // Process data securely
                return Ok("Processed successfully");
            }
            catch (Exception)
            {
                // Log internally, return generic message
                return InternalServerError();
            }
        }

        // SAFE: Using secure hash algorithm
        public string HashData(string data)
        {
            using (var sha256 = SHA256.Create())
            {
                var bytes = Encoding.UTF8.GetBytes(data);
                var hash = sha256.ComputeHash(bytes);
                return Convert.ToBase64String(hash);
            }
        }

        // SAFE: Proper CORS with specific origin
        public void ConfigureSecureCors()
        {
            // Would use specific origins, not wildcards
            var allowedOrigins = new[] { "https://trusted-app.com" };
        }
    }

    public class DataRequest
    {
        public string Data { get; set; }
    }
}
