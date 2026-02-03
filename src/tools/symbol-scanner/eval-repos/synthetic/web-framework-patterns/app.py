"""Web framework patterns - Flask/FastAPI style routes and middleware."""

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable


# ============================================================================
# Request/Response Models
# ============================================================================


@dataclass
class Request:
    """HTTP Request model."""

    method: str
    path: str
    headers: dict[str, str]
    body: Any = None
    query_params: dict[str, str] | None = None

    def get_header(self, name: str, default: str = "") -> str:
        """Get header value."""
        return self.headers.get(name, default)


@dataclass
class Response:
    """HTTP Response model."""

    status_code: int = 200
    body: Any = None
    headers: dict[str, str] | None = None

    @classmethod
    def json(cls, data: dict, status: int = 200) -> "Response":
        """Create JSON response."""
        return cls(status_code=status, body=data)

    @classmethod
    def error(cls, message: str, status: int = 500) -> "Response":
        """Create error response."""
        return cls(status_code=status, body={"error": message})


# ============================================================================
# Route Decorators
# ============================================================================


class Router:
    """Simple router for handling HTTP routes."""

    def __init__(self) -> None:
        """Initialize router."""
        self.routes: dict[str, dict[str, Callable]] = {}
        self.middleware: list[Callable] = []

    def route(self, path: str, methods: list[str] | None = None) -> Callable:
        """Decorator to register a route."""
        methods = methods or ["GET"]

        def decorator(func: Callable) -> Callable:
            for method in methods:
                if path not in self.routes:
                    self.routes[path] = {}
                self.routes[path][method] = func
            return func

        return decorator

    def get(self, path: str) -> Callable:
        """Decorator for GET routes."""
        return self.route(path, ["GET"])

    def post(self, path: str) -> Callable:
        """Decorator for POST routes."""
        return self.route(path, ["POST"])

    def put(self, path: str) -> Callable:
        """Decorator for PUT routes."""
        return self.route(path, ["PUT"])

    def delete(self, path: str) -> Callable:
        """Decorator for DELETE routes."""
        return self.route(path, ["DELETE"])

    def use(self, middleware: Callable) -> None:
        """Add middleware."""
        self.middleware.append(middleware)

    def handle(self, request: Request) -> Response:
        """Handle incoming request."""
        path_routes = self.routes.get(request.path)
        if not path_routes:
            return Response.error("Not found", 404)

        handler = path_routes.get(request.method)
        if not handler:
            return Response.error("Method not allowed", 405)

        # Apply middleware
        final_handler = handler
        for mw in reversed(self.middleware):
            final_handler = mw(final_handler)

        return final_handler(request)


# ============================================================================
# Middleware Functions
# ============================================================================


def logging_middleware(handler: Callable) -> Callable:
    """Middleware that logs requests."""
    @wraps(handler)
    def wrapper(request: Request) -> Response:
        print(f"{request.method} {request.path}")
        response = handler(request)
        print(f"Status: {response.status_code}")
        return response
    return wrapper


def auth_middleware(handler: Callable) -> Callable:
    """Middleware that checks authentication."""
    @wraps(handler)
    def wrapper(request: Request) -> Response:
        token = request.get_header("Authorization")
        if not token or not token.startswith("Bearer "):
            return Response.error("Unauthorized", 401)
        return handler(request)
    return wrapper


def cors_middleware(handler: Callable) -> Callable:
    """Middleware that adds CORS headers."""
    @wraps(handler)
    def wrapper(request: Request) -> Response:
        response = handler(request)
        if response.headers is None:
            response.headers = {}
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    return wrapper


def rate_limit_middleware(max_requests: int = 100) -> Callable:
    """Configurable rate limiting middleware."""
    request_counts: dict[str, int] = {}

    def middleware(handler: Callable) -> Callable:
        @wraps(handler)
        def wrapper(request: Request) -> Response:
            client_ip = request.get_header("X-Forwarded-For", "unknown")
            count = request_counts.get(client_ip, 0)
            if count >= max_requests:
                return Response.error("Rate limit exceeded", 429)
            request_counts[client_ip] = count + 1
            return handler(request)
        return wrapper
    return middleware


# ============================================================================
# Dependency Injection
# ============================================================================


class Container:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        """Initialize container."""
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable] = {}

    def register(self, name: str, service: Any) -> None:
        """Register a service instance."""
        self._services[name] = service

    def register_factory(self, name: str, factory: Callable) -> None:
        """Register a service factory."""
        self._factories[name] = factory

    def get(self, name: str) -> Any:
        """Get a service."""
        if name in self._services:
            return self._services[name]
        if name in self._factories:
            service = self._factories[name]()
            self._services[name] = service
            return service
        raise KeyError(f"Service not found: {name}")


def inject(*dependencies: str) -> Callable:
    """Decorator for dependency injection."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, container: Container, **kwargs) -> Any:
            injected = {dep: container.get(dep) for dep in dependencies}
            return func(*args, **injected, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# Application Routes
# ============================================================================


app = Router()


@app.get("/")
def index(request: Request) -> Response:
    """Home page handler."""
    return Response.json({"message": "Welcome"})


@app.get("/users")
def list_users(request: Request) -> Response:
    """List all users."""
    users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    return Response.json({"users": users})


@app.get("/users/{id}")
def get_user(request: Request) -> Response:
    """Get single user."""
    return Response.json({"id": 1, "name": "Alice"})


@app.post("/users")
def create_user(request: Request) -> Response:
    """Create a new user."""
    if not request.body:
        return Response.error("Body required", 400)
    return Response.json({"id": 3, "name": request.body.get("name")}, status=201)


@app.put("/users/{id}")
def update_user(request: Request) -> Response:
    """Update a user."""
    return Response.json({"updated": True})


@app.delete("/users/{id}")
def delete_user(request: Request) -> Response:
    """Delete a user."""
    return Response.json({"deleted": True})


# ============================================================================
# Service Classes
# ============================================================================


class UserService:
    """User service for business logic."""

    def __init__(self, repository: Any):
        """Initialize with repository."""
        self.repository = repository

    def get_all(self) -> list[dict]:
        """Get all users."""
        return self.repository.find_all()

    def get_by_id(self, user_id: int) -> dict | None:
        """Get user by ID."""
        return self.repository.find_by_id(user_id)

    def create(self, data: dict) -> dict:
        """Create a user."""
        return self.repository.save(data)

    def update(self, user_id: int, data: dict) -> dict | None:
        """Update a user."""
        user = self.repository.find_by_id(user_id)
        if not user:
            return None
        user.update(data)
        return self.repository.save(user)

    def delete(self, user_id: int) -> bool:
        """Delete a user."""
        return self.repository.delete(user_id)
