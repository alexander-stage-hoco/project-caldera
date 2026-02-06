// Security Misconfiguration test cases for DevSkim evaluation
// Expected: Custom DevSkim rules should detect insecure configurations

using System;
using System.Web;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;

namespace SecurityTests
{
    public class SecurityMisconfigurations
    {
        // VULNERABLE: Cookie with HttpOnly disabled (CALDERA007)
        public void SetInsecureCookie(HttpResponse response)
        {
            var cookie = new Cookie("session", "abc123");
            cookie.HttpOnly = false;  // Allows JavaScript access
            response.Cookies.Append("session", "abc123", new CookieOptions
            {
                HttpOnly = false  // DevSkim should flag this
            });
        }

        // VULNERABLE: Cookie with Secure flag disabled (CALDERA008)
        public void SetNonSecureCookie(HttpResponse response)
        {
            response.Cookies.Append("auth", "token123", new CookieOptions
            {
                Secure = false  // Allows transmission over HTTP
            });
        }

        // VULNERABLE: Permissive CORS configuration (CALDERA009)
        public void ConfigureCors(IApplicationBuilder app)
        {
            app.UseCors(builder => builder.AllowAnyOrigin()  // Allows all origins
                                          .AllowAnyMethod()
                                          .AllowAnyHeader());
        }

        // VULNERABLE: Wildcard Access-Control-Allow-Origin
        public void SetCorsHeader(HttpResponse response)
        {
            response.Headers.Add("Access-Control-Allow-Origin", "*");  // Wildcard origin
        }

        // VULNERABLE: Shell command execution (CALDERA006)
        public void RunShellCommand(string userInput)
        {
            var process = new System.Diagnostics.ProcessStartInfo
            {
                FileName = "cmd.exe",  // Shell command execution
                Arguments = "/c " + userInput
            };
            System.Diagnostics.Process.Start(process);
        }

        // SAFE: Cookie with HttpOnly enabled
        public void SetSecureCookie(HttpResponse response)
        {
            response.Cookies.Append("session", "abc123", new CookieOptions
            {
                HttpOnly = true,
                Secure = true,
                SameSite = SameSiteMode.Strict
            });
            // This should NOT be flagged
        }

        // SAFE: Specific CORS origin
        public void ConfigureSecureCors(IApplicationBuilder app)
        {
            app.UseCors(builder => builder.WithOrigins("https://example.com")
                                          .AllowAnyMethod()
                                          .AllowAnyHeader());
            // This should NOT be flagged
        }
    }
}
