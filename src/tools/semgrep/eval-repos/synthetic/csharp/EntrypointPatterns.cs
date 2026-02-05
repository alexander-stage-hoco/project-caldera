/**
 * Test file for Elttam entrypoint discovery patterns.
 * Contains ASP.NET controller and route patterns.
 */

using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using System.Threading.Tasks;

namespace Synthetic.Controllers
{
    // ENTRYPOINT_DISCOVERY: ASP.NET MVC Controller
    [ApiController]
    [Route("api/[controller]")]
    public class UsersController : ControllerBase
    {
        // ENTRYPOINT_DISCOVERY: HttpGet endpoint
        [HttpGet]
        public IActionResult GetAll()
        {
            return Ok(new { message = "Get all users" });
        }

        // ENTRYPOINT_DISCOVERY: HttpGet with parameter
        [HttpGet("{id}")]
        public IActionResult GetById(int id)
        {
            return Ok(new { id = id });
        }

        // ENTRYPOINT_DISCOVERY: HttpPost endpoint
        [HttpPost]
        public IActionResult Create([FromBody] object user)
        {
            return Created("", user);
        }

        // ENTRYPOINT_DISCOVERY: HttpPut endpoint
        [HttpPut("{id}")]
        public IActionResult Update(int id, [FromBody] object user)
        {
            return Ok(new { id = id, updated = true });
        }

        // ENTRYPOINT_DISCOVERY: HttpDelete endpoint
        [HttpDelete("{id}")]
        public IActionResult Delete(int id)
        {
            return NoContent();
        }
    }

    // ENTRYPOINT_DISCOVERY: MVC Controller
    public class HomeController : Controller
    {
        // ENTRYPOINT_DISCOVERY: Action method
        public IActionResult Index()
        {
            return View();
        }

        // ENTRYPOINT_DISCOVERY: Action with route
        [Route("about")]
        public IActionResult About()
        {
            return View();
        }
    }

    // ENTRYPOINT_DISCOVERY: Authorized controller
    [Authorize]
    [Route("api/admin")]
    public class AdminController : ControllerBase
    {
        // AUDIT_AUTH_CHECK: Endpoint requiring authorization
        [HttpGet("dashboard")]
        public IActionResult Dashboard()
        {
            return Ok(new { message = "Admin dashboard" });
        }

        // AUDIT_AUTH_CHECK: Role-based authorization
        [Authorize(Roles = "SuperAdmin")]
        [HttpPost("settings")]
        public IActionResult UpdateSettings([FromBody] object settings)
        {
            return Ok(settings);
        }
    }

    // ENTRYPOINT_DISCOVERY: Minimal API endpoints
    public static class MinimalApiEndpoints
    {
        public static void MapEndpoints(WebApplication app)
        {
            // ENTRYPOINT_DISCOVERY: Minimal API route
            app.MapGet("/api/health", () => Results.Ok(new { status = "healthy" }));

            // ENTRYPOINT_DISCOVERY: Minimal API with parameter
            app.MapGet("/api/items/{id}", (int id) => Results.Ok(new { id }));

            // ENTRYPOINT_DISCOVERY: Minimal API POST
            app.MapPost("/api/items", (object item) => Results.Created("/api/items/1", item));
        }
    }
}
