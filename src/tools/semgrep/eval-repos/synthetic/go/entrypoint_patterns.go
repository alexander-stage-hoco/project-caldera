// Test file for Elttam entrypoint discovery patterns.
// Contains net/http, Gin, Echo, and Chi entrypoint patterns.
package synthetic

import (
	"encoding/json"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/go-chi/chi"
	"github.com/gorilla/mux"
	"github.com/labstack/echo/v4"
)

// ENTRYPOINT_DISCOVERY: net/http HandleFunc
func setupHttpHandlers() {
	http.HandleFunc("/", homeHandler)
	http.HandleFunc("/api/users", usersHandler)
	http.HandleFunc("/api/users/", userByIdHandler)
}

// ENTRYPOINT_DISCOVERY: http.Handler implementation
type HomeHandler struct{}

func (h *HomeHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{"message": "Home"})
}

// ENTRYPOINT_DISCOVERY: HTTP handler function
func homeHandler(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{"message": "Home"})
}

// ENTRYPOINT_DISCOVERY: HTTP handler with method check
func usersHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		json.NewEncoder(w).Encode(map[string]interface{}{"users": []string{}})
	case http.MethodPost:
		json.NewEncoder(w).Encode(map[string]bool{"created": true})
	}
}

func userByIdHandler(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{"user": "details"})
}

// ENTRYPOINT_DISCOVERY: Gin router setup
func setupGinRoutes() *gin.Engine {
	r := gin.Default()

	// ENTRYPOINT_DISCOVERY: Gin GET route
	r.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "Home"})
	})

	// ENTRYPOINT_DISCOVERY: Gin route with parameter
	r.GET("/users/:id", func(c *gin.Context) {
		id := c.Param("id")
		c.JSON(200, gin.H{"id": id})
	})

	// ENTRYPOINT_DISCOVERY: Gin POST route
	r.POST("/users", func(c *gin.Context) {
		c.JSON(201, gin.H{"created": true})
	})

	// ENTRYPOINT_DISCOVERY: Gin route group
	api := r.Group("/api")
	{
		api.GET("/products", func(c *gin.Context) {
			c.JSON(200, gin.H{"products": []string{}})
		})
	}

	return r
}

// ENTRYPOINT_DISCOVERY: Echo router setup
func setupEchoRoutes() *echo.Echo {
	e := echo.New()

	// ENTRYPOINT_DISCOVERY: Echo GET route
	e.GET("/", func(c echo.Context) error {
		return c.JSON(200, map[string]string{"message": "Home"})
	})

	// ENTRYPOINT_DISCOVERY: Echo route with parameter
	e.GET("/users/:id", func(c echo.Context) error {
		id := c.Param("id")
		return c.JSON(200, map[string]string{"id": id})
	})

	// ENTRYPOINT_DISCOVERY: Echo POST route
	e.POST("/users", func(c echo.Context) error {
		return c.JSON(201, map[string]bool{"created": true})
	})

	return e
}

// ENTRYPOINT_DISCOVERY: Chi router setup
func setupChiRoutes() *chi.Mux {
	r := chi.NewRouter()

	// ENTRYPOINT_DISCOVERY: Chi GET route
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]string{"message": "Home"})
	})

	// ENTRYPOINT_DISCOVERY: Chi route with parameter
	r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		json.NewEncoder(w).Encode(map[string]string{"id": id})
	})

	// ENTRYPOINT_DISCOVERY: Chi POST route
	r.Post("/users", func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]bool{"created": true})
	})

	return r
}

// ENTRYPOINT_DISCOVERY: Gorilla mux router
func setupGorillaMuxRoutes() *mux.Router {
	r := mux.NewRouter()

	// ENTRYPOINT_DISCOVERY: Gorilla route
	r.HandleFunc("/", homeHandler).Methods("GET")
	r.HandleFunc("/users/{id}", userByIdHandler).Methods("GET")
	r.HandleFunc("/users", usersHandler).Methods("GET", "POST")

	return r
}

// AUDIT_INPUT_SINK: User input handling
func processInput(w http.ResponseWriter, r *http.Request) {
	userInput := r.FormValue("input") // AUDIT_INPUT_SINK
	_ = userInput
}

// AUDIT_FILE_UPLOAD: File upload handling
func handleFileUpload(w http.ResponseWriter, r *http.Request) {
	file, header, err := r.FormFile("file") // AUDIT_FILE_UPLOAD
	if err != nil {
		return
	}
	defer file.Close()
	_ = header
}
