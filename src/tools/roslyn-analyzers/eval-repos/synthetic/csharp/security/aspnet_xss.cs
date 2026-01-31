using System;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Html;

namespace SyntheticSmells.Security
{
    /// <summary>
    /// ASP.NET Core XSS vulnerability examples for CA3002 detection.
    /// These patterns represent unsafe HTML output that should trigger XSS warnings.
    /// </summary>
    public class XssController : Controller
    {
        // Vulnerable: Html.Raw with user input (CA3002)
        public IActionResult VulnerableRawHtml(string userInput)
        {
            ViewBag.UserContent = new HtmlString(userInput);  // CA3002: XSS
            return View();
        }

        // Vulnerable: Direct raw HTML output via Content
        public IActionResult VulnerableContentHtml(string name)
        {
            return Content($"<h1>Welcome {name}</h1>", "text/html");  // CA3002: XSS
        }

        // Vulnerable: String concatenation in HTML response
        public IActionResult VulnerableHtmlResponse(string message)
        {
            var html = "<div class='alert'>" + message + "</div>";  // CA3002: XSS
            return Content(html, "text/html");
        }

        // Vulnerable: Interpolated string in HTML
        public IActionResult VulnerableInterpolation(string title)
        {
            return Content($"<title>{title}</title>", "text/html");  // CA3002: XSS
        }

        // SAFE: Using HtmlEncoder (no violation expected)
        public IActionResult SafeEncodedOutput(string userInput)
        {
            var encoded = System.Text.Encodings.Web.HtmlEncoder.Default.Encode(userInput);
            return Content($"<div>{encoded}</div>", "text/html");
        }

        // SAFE: Returning JSON instead of HTML
        public IActionResult SafeJsonResponse(string data)
        {
            return Json(new { message = data });
        }
    }
}
