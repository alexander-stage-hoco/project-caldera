// Package simple demonstrates basic Go patterns.
package simple

import (
	"fmt"
	"strings"
)

// User represents a system user.
type User struct {
	ID    int
	Name  string
	Email string
	Active bool
}

// Greet returns a greeting message for the user.
func (u *User) Greet() string {
	return fmt.Sprintf("Hello, %s!", u.Name)
}

// IsValid checks if the user has valid data.
func (u *User) IsValid() bool {
	return u.ID > 0 && u.Name != "" && strings.Contains(u.Email, "@")
}

// Counter is a simple counter implementation.
type Counter struct {
	value int
}

// NewCounter creates a new counter with initial value.
func NewCounter(initial int) *Counter {
	return &Counter{value: initial}
}

// Increment increases the counter by 1.
func (c *Counter) Increment() {
	c.value++
}

// Decrement decreases the counter by 1.
func (c *Counter) Decrement() {
	c.value--
}

// Value returns the current counter value.
func (c *Counter) Value() int {
	return c.value
}

// Add sums two integers.
func Add(a, b int) int {
	return a + b
}

// Multiply multiplies two integers.
func Multiply(a, b int) int {
	return a * b
}

// Divide divides a by b, returns error if b is zero.
func Divide(a, b int) (int, error) {
	if b == 0 {
		return 0, fmt.Errorf("division by zero")
	}
	return a / b, nil
}

// FilterActiveUsers returns only active users from the slice.
func FilterActiveUsers(users []User) []User {
	var active []User
	for _, u := range users {
		if u.Active {
			active = append(active, u)
		}
	}
	return active
}

// MapUserNames extracts names from a slice of users.
func MapUserNames(users []User) []string {
	names := make([]string, len(users))
	for i, u := range users {
		names[i] = u.Name
	}
	return names
}
