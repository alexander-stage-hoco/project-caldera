using System;
using System.Net;
using System.Net.Security;
using System.Security.Authentication;

namespace SyntheticSmells.Security
{
    /// <summary>
    /// Deprecated TLS/SSL protocol examples for Roslyn Analyzer testing.
    /// Expected violations: CA5364 (2), CA5397 (1) = 3 total
    /// Safe patterns: 2
    /// </summary>
    public class DeprecatedTlsExamples
    {
        // CA5364: Deprecated TLS 1.0 (line 17)
        public void UseTls10()
        {
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls;
        }

        // CA5364: Deprecated TLS 1.1 (line 24)
        public void UseTls11()
        {
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls11;
        }

        // CA5397: Deprecated SSL 3.0 (line 31)
        public void UseSsl3()
        {
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Ssl3;
        }

        // SAFE: Using TLS 1.2 (no violation expected)
        public void SecureUseTls12()
        {
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
        }

        // SAFE: Using TLS 1.3 or system default (no violation expected)
        public void SecureUseTls13()
        {
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12 | SecurityProtocolType.Tls13;
        }
    }
}
