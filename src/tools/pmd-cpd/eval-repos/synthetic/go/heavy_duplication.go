// Package synthetic contains Go files for CPD testing with heavy duplication.
package synthetic

import (
	"fmt"
	"strings"
)

// ReportItem represents an item in a report.
type ReportItem struct {
	ID        string
	Name      string
	Email     string
	Status    string
	CreatedAt string
}

// GenerateUserReport creates a formatted report for users.
func GenerateUserReport(users []ReportItem) string {
	var lines []string
	lines = append(lines, strings.Repeat("=", 60))
	lines = append(lines, "USER REPORT")
	lines = append(lines, strings.Repeat("=", 60))
	lines = append(lines, "")

	for _, item := range users {
		id := item.ID
		if id == "" {
			id = "N/A"
		}
		name := item.Name
		if name == "" {
			name = "Unknown"
		}
		email := item.Email
		if email == "" {
			email = "N/A"
		}
		status := item.Status
		if status == "" {
			status = "active"
		}
		createdAt := item.CreatedAt
		if createdAt == "" {
			createdAt = "Unknown"
		}
		lines = append(lines, fmt.Sprintf("ID: %s", id))
		lines = append(lines, fmt.Sprintf("Name: %s", name))
		lines = append(lines, fmt.Sprintf("Email: %s", email))
		lines = append(lines, fmt.Sprintf("Status: %s", status))
		lines = append(lines, fmt.Sprintf("Created: %s", createdAt))
		lines = append(lines, strings.Repeat("-", 40))
	}

	lines = append(lines, "")
	lines = append(lines, fmt.Sprintf("Total records: %d", len(users)))
	lines = append(lines, strings.Repeat("=", 60))
	return strings.Join(lines, "\n")
}

// GenerateAdminReport creates a formatted report for admins - duplicated structure.
func GenerateAdminReport(admins []ReportItem) string {
	var lines []string
	lines = append(lines, strings.Repeat("=", 60))
	lines = append(lines, "ADMIN REPORT")
	lines = append(lines, strings.Repeat("=", 60))
	lines = append(lines, "")

	for _, item := range admins {
		id := item.ID
		if id == "" {
			id = "N/A"
		}
		name := item.Name
		if name == "" {
			name = "Unknown"
		}
		email := item.Email
		if email == "" {
			email = "N/A"
		}
		status := item.Status
		if status == "" {
			status = "active"
		}
		createdAt := item.CreatedAt
		if createdAt == "" {
			createdAt = "Unknown"
		}
		lines = append(lines, fmt.Sprintf("ID: %s", id))
		lines = append(lines, fmt.Sprintf("Name: %s", name))
		lines = append(lines, fmt.Sprintf("Email: %s", email))
		lines = append(lines, fmt.Sprintf("Status: %s", status))
		lines = append(lines, fmt.Sprintf("Created: %s", createdAt))
		lines = append(lines, strings.Repeat("-", 40))
	}

	lines = append(lines, "")
	lines = append(lines, fmt.Sprintf("Total records: %d", len(admins)))
	lines = append(lines, strings.Repeat("=", 60))
	return strings.Join(lines, "\n")
}

// GenerateGuestReport creates a formatted report for guests - duplicated structure.
func GenerateGuestReport(guests []ReportItem) string {
	var lines []string
	lines = append(lines, strings.Repeat("=", 60))
	lines = append(lines, "GUEST REPORT")
	lines = append(lines, strings.Repeat("=", 60))
	lines = append(lines, "")

	for _, item := range guests {
		id := item.ID
		if id == "" {
			id = "N/A"
		}
		name := item.Name
		if name == "" {
			name = "Unknown"
		}
		email := item.Email
		if email == "" {
			email = "N/A"
		}
		status := item.Status
		if status == "" {
			status = "active"
		}
		createdAt := item.CreatedAt
		if createdAt == "" {
			createdAt = "Unknown"
		}
		lines = append(lines, fmt.Sprintf("ID: %s", id))
		lines = append(lines, fmt.Sprintf("Name: %s", name))
		lines = append(lines, fmt.Sprintf("Email: %s", email))
		lines = append(lines, fmt.Sprintf("Status: %s", status))
		lines = append(lines, fmt.Sprintf("Created: %s", createdAt))
		lines = append(lines, strings.Repeat("-", 40))
	}

	lines = append(lines, "")
	lines = append(lines, fmt.Sprintf("Total records: %d", len(guests)))
	lines = append(lines, strings.Repeat("=", 60))
	return strings.Join(lines, "\n")
}

// InputData represents input data for validation.
type InputData struct {
	Name     string
	Email    string
	Password string
	Age      int
}

// ValidateUserInput validates user input data.
func ValidateUserInput(data InputData) []string {
	var errors []string
	if data.Name == "" {
		errors = append(errors, "Name is required")
	}
	if data.Email == "" {
		errors = append(errors, "Email is required")
	}
	if !strings.Contains(data.Email, "@") {
		errors = append(errors, "Invalid email format")
	}
	if data.Password == "" {
		errors = append(errors, "Password is required")
	}
	if len(data.Password) < 8 {
		errors = append(errors, "Password must be at least 8 characters")
	}
	if data.Age == 0 {
		errors = append(errors, "Age is required")
	}
	if data.Age < 18 {
		errors = append(errors, "Must be at least 18 years old")
	}
	return errors
}

// ValidateAdminInput validates admin input data - duplicated validation.
func ValidateAdminInput(data InputData) []string {
	var errors []string
	if data.Name == "" {
		errors = append(errors, "Name is required")
	}
	if data.Email == "" {
		errors = append(errors, "Email is required")
	}
	if !strings.Contains(data.Email, "@") {
		errors = append(errors, "Invalid email format")
	}
	if data.Password == "" {
		errors = append(errors, "Password is required")
	}
	if len(data.Password) < 8 {
		errors = append(errors, "Password must be at least 8 characters")
	}
	if data.Age == 0 {
		errors = append(errors, "Age is required")
	}
	if data.Age < 18 {
		errors = append(errors, "Must be at least 18 years old")
	}
	return errors
}
