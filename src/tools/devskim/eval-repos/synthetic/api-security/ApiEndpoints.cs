// API Endpoint security test cases for DevSkim evaluation
// Expected: DevSkim should detect insecure API patterns

using System;
using System.Web.Http;
using System.Net.Http;

namespace ApiSecurity
{
    public class ApiEndpoints : ApiController
    {
        // VULNERABLE: Exposing internal error details
        [HttpGet]
        [Route("api/users/{id}")]
        public IHttpActionResult GetUser(int id)
        {
            try
            {
                // Some database operation
                throw new Exception("Database connection failed");
            }
            catch (Exception ex)
            {
                // Exposing stack trace to client
                return InternalServerError(ex);
            }
        }

        // VULNERABLE: Missing authorization attribute
        [HttpDelete]
        [Route("api/admin/users/{id}")]
        public IHttpActionResult DeleteUser(int id)
        {
            // No [Authorize] attribute - admin endpoint unprotected
            return Ok($"User {id} deleted");
        }

        // VULNERABLE: Verbose error messages
        [HttpPost]
        [Route("api/login")]
        public IHttpActionResult Login(string username, string password)
        {
            if (username != "admin")
            {
                return BadRequest("User 'admin' not found in database");  // Info disclosure
            }
            if (password != "secret")
            {
                return BadRequest("Invalid password for user 'admin'");  // Info disclosure
            }
            return Ok("Logged in");
        }

        // VULNERABLE: Missing rate limiting on sensitive endpoint
        [HttpPost]
        [Route("api/password/reset")]
        public IHttpActionResult ResetPassword(string email)
        {
            // No rate limiting - brute force possible
            // DevSkim may flag missing security controls
            return Ok("Password reset email sent");
        }

        // VULNERABLE: HTTP method override allowing bypass
        [HttpGet]
        [Route("api/data")]
        public IHttpActionResult GetData()
        {
            // X-HTTP-Method-Override can bypass method restrictions
            var methodOverride = Request.Headers.Contains("X-HTTP-Method-Override");
            return Ok("Data retrieved");
        }

        // SAFE: Proper error handling (no finding expected)
        [HttpGet]
        [Route("api/products/{id}")]
        public IHttpActionResult GetProduct(int id)
        {
            try
            {
                // Database operation
                return Ok("Product data");
            }
            catch (Exception)
            {
                // Generic error message - no details exposed
                return InternalServerError();
            }
        }

        // SAFE: With authorization
        [Authorize(Roles = "Admin")]
        [HttpDelete]
        [Route("api/admin/products/{id}")]
        public IHttpActionResult DeleteProduct(int id)
        {
            // Properly protected with authorization
            return Ok("Product deleted");
        }
    }
}
