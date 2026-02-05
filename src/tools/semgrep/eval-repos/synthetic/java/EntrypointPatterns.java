/**
 * Test file for Elttam entrypoint discovery patterns.
 * Contains Spring MVC, JAX-RS, and Servlet entrypoint patterns.
 */
package synthetic.java;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
import javax.servlet.http.*;
import java.io.IOException;

// ENTRYPOINT_DISCOVERY: Spring REST Controller
@RestController
@RequestMapping("/api/users")
public class UsersController {

    // ENTRYPOINT_DISCOVERY: Spring GetMapping
    @GetMapping
    public ResponseEntity<?> getAllUsers() {
        return ResponseEntity.ok().body("All users");
    }

    // ENTRYPOINT_DISCOVERY: Spring GetMapping with path variable
    @GetMapping("/{id}")
    public ResponseEntity<?> getUserById(@PathVariable Long id) {
        return ResponseEntity.ok().body("User " + id);
    }

    // ENTRYPOINT_DISCOVERY: Spring PostMapping
    @PostMapping
    public ResponseEntity<?> createUser(@RequestBody Object user) {
        return ResponseEntity.created(null).body(user);
    }

    // ENTRYPOINT_DISCOVERY: Spring PutMapping
    @PutMapping("/{id}")
    public ResponseEntity<?> updateUser(@PathVariable Long id, @RequestBody Object user) {
        return ResponseEntity.ok().body("Updated user " + id);
    }

    // ENTRYPOINT_DISCOVERY: Spring DeleteMapping
    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteUser(@PathVariable Long id) {
        return ResponseEntity.noContent().build();
    }

    // AUDIT_AUTH_CHECK: PreAuthorize annotation
    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping("/admin")
    public ResponseEntity<?> adminEndpoint() {
        return ResponseEntity.ok().body("Admin only");
    }
}

// ENTRYPOINT_DISCOVERY: Spring MVC Controller
@Controller
public class HomeController {

    // ENTRYPOINT_DISCOVERY: RequestMapping
    @RequestMapping("/")
    public String home() {
        return "home";
    }

    // ENTRYPOINT_DISCOVERY: RequestMapping with method
    @RequestMapping(value = "/about", method = RequestMethod.GET)
    public String about() {
        return "about";
    }
}

// ENTRYPOINT_DISCOVERY: JAX-RS Resource
@Path("/api/products")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class ProductResource {

    // ENTRYPOINT_DISCOVERY: JAX-RS GET
    @GET
    public String getProducts() {
        return "[]";
    }

    // ENTRYPOINT_DISCOVERY: JAX-RS GET with path param
    @GET
    @Path("/{id}")
    public String getProduct(@PathParam("id") Long id) {
        return "Product " + id;
    }

    // ENTRYPOINT_DISCOVERY: JAX-RS POST
    @POST
    public String createProduct(Object product) {
        return "Created";
    }
}

// ENTRYPOINT_DISCOVERY: Servlet mapping
public class OrderServlet extends HttpServlet {

    // ENTRYPOINT_DISCOVERY: Servlet doGet
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        resp.getWriter().write("Orders list");
    }

    // ENTRYPOINT_DISCOVERY: Servlet doPost
    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        resp.getWriter().write("Order created");
    }

    // AUDIT_INPUT_SINK: User input handling
    private void processInput(HttpServletRequest req) {
        String userInput = req.getParameter("input"); // AUDIT_INPUT_SINK
    }
}

// Struts Action pattern (legacy)
// ENTRYPOINT_DISCOVERY: Struts Action
public class UserAction {
    public String execute() {
        return "success";
    }

    public String list() {
        return "list";
    }
}
