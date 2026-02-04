// CORS Configuration test cases for DevSkim evaluation
// Expected: DevSkim should detect insecure CORS patterns

using System;
using System.Web.Http;
using System.Web.Http.Cors;

namespace ApiSecurity
{
    public class CorsConfig
    {
        // VULNERABLE: Wildcard CORS origin allows any domain (DS137138)
        public void ConfigureInsecureCors(HttpConfiguration config)
        {
            var cors = new EnableCorsAttribute("*", "*", "*");
            config.EnableCors(cors);
            // DevSkim should flag wildcard origin as security risk
        }

        // VULNERABLE: Allowing credentials with wildcard origin
        public void ConfigureCredentialsCors(HttpConfiguration config)
        {
            var cors = new EnableCorsAttribute("*", "*", "GET,POST,PUT,DELETE");
            cors.SupportsCredentials = true;  // Dangerous with wildcard
            config.EnableCors(cors);
        }

        // VULNERABLE: Exposing all headers
        public void ConfigureExposedHeaders(HttpConfiguration config)
        {
            var cors = new EnableCorsAttribute("*", "*", "*");
            // Exposing sensitive headers to any origin
            config.EnableCors(cors);
        }

        // SAFE: Specific origin CORS (no finding expected)
        public void ConfigureSecureCors(HttpConfiguration config)
        {
            var cors = new EnableCorsAttribute(
                "https://trusted-domain.com",
                "Content-Type,Authorization",
                "GET,POST"
            );
            config.EnableCors(cors);
            // This should NOT be flagged - specific origin
        }

        // SAFE: No CORS configuration
        public void NoCorsConfig(HttpConfiguration config)
        {
            // Default - no CORS enabled
            // This should NOT be flagged
        }
    }
}
