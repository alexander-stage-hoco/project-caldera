using System;
using System.Net;
using System.Text;
using System.IO;
using System.Web;

namespace SyntheticSmells.Security
{
    /// <summary>
    /// XSS vulnerability examples for Roslyn Analyzer testing.
    /// These patterns represent unsafe HTML output that could lead to XSS.
    /// Note: CA3002 requires sophisticated data flow analysis. SCS0029 from
    /// SecurityCodeScan provides pattern-based detection for Response.Write.
    /// </summary>
    public class XssVulnerabilityExamples
    {
        // Vulnerable: Direct user input in HTML without encoding (CA3002)
        public string VulnerableResponse1(string userInput)
        {
            return "<div>" + userInput + "</div>";
        }

        // Vulnerable: String interpolation with user input in HTML (CA3002)
        public string VulnerableHtmlBuilder(string userName)
        {
            return $"<span class='username'>{userName}</span>";
        }

        // Vulnerable: Script injection pattern (CA3002)
        public string VulnerableScriptInjection(string callback)
        {
            return $"<script>callback('{callback}')</script>";
        }

        // Vulnerable: Event handler injection (CA3002)
        public string VulnerableEventHandler(string handler)
        {
            return $"<button onclick='{handler}'>Click</button>";
        }

        // SCS0029: Response.Write with user input (SecurityCodeScan XSS detection)
        public void WriteToResponse1(string userInput, HttpResponse response)
        {
            response.Write(userInput);  // SCS0029: XSS via Response.Write
        }

        // SCS0029: Response.Write with concatenation
        public void WriteToResponse2(string name, HttpResponse response)
        {
            response.Write("<h1>" + name + "</h1>");  // SCS0029: XSS
        }

        // SCS0029: Response.Write with interpolation
        public void WriteToResponse3(string message, HttpResponse response)
        {
            response.Write($"<div class='alert'>{message}</div>");  // SCS0029: XSS
        }

        // SCS0029: Response.Write with StringBuilder
        public void WriteToResponse4(string content, HttpResponse response)
        {
            var sb = new StringBuilder();
            sb.Append("<p>").Append(content).Append("</p>");
            response.Write(sb.ToString());  // SCS0029: XSS
        }

        // SAFE: HTML encoded output (no violation expected)
        public string SafeEncodedOutput(string userInput)
        {
            return "<div>" + WebUtility.HtmlEncode(userInput) + "</div>";
        }

        // SAFE: Using proper encoding
        public string SafePattern(string userInput)
        {
            var encoded = WebUtility.HtmlEncode(userInput);
            return $"<div>{encoded}</div>";
        }

        // SAFE: HttpUtility.HtmlEncode before Response.Write
        public void SafeResponseWrite(string userInput, HttpResponse response)
        {
            response.Write(HttpUtility.HtmlEncode(userInput));
        }
    }
}

// Minimal System.Web stub for compilation
namespace System.Web
{
    public class HttpResponse
    {
        public void Write(string s) { }
        public void Write(object obj) { }
    }

    public static class HttpUtility
    {
        public static string HtmlEncode(string s) => System.Net.WebUtility.HtmlEncode(s);
    }
}
