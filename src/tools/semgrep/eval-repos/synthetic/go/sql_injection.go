// Test file for SQL injection vulnerability detection.
// Contains multiple SQL injection patterns.
package smells

import (
	"database/sql"
	"fmt"
)

// GetUserByName has SQL injection vulnerability
// SQL INJECTION: String formatting in query
func GetUserByName(db *sql.DB, username string) (*sql.Row, error) {
	query := fmt.Sprintf("SELECT * FROM users WHERE username = '%s'", username)
	return db.QueryRow(query), nil
}

// SearchProducts has SQL injection vulnerability
// SQL INJECTION: String concatenation
func SearchProducts(db *sql.DB, searchTerm string) (*sql.Rows, error) {
	query := "SELECT * FROM products WHERE name LIKE '%" + searchTerm + "%'"
	return db.Query(query)
}

// DeleteUser has SQL injection vulnerability
// SQL INJECTION: Direct string interpolation
func DeleteUser(db *sql.DB, userID string) error {
	query := fmt.Sprintf("DELETE FROM users WHERE id = %s", userID)
	_, err := db.Exec(query)
	return err
}

// UpdateEmail has SQL injection vulnerability
// SQL INJECTION: Multiple injectable parameters
func UpdateEmail(db *sql.DB, userID string, email string) error {
	query := fmt.Sprintf("UPDATE users SET email = '%s' WHERE id = %s", email, userID)
	_, err := db.Exec(query)
	return err
}

// GetOrdersByDate has SQL injection vulnerability
// SQL INJECTION: Multiple string interpolations
func GetOrdersByDate(db *sql.DB, startDate, endDate string) (*sql.Rows, error) {
	query := "SELECT * FROM orders WHERE created_at BETWEEN '" + startDate + "' AND '" + endDate + "'"
	return db.Query(query)
}

// FindUserByEmail has SQL injection vulnerability
// SQL INJECTION: Another interpolation pattern
func FindUserByEmail(db *sql.DB, email string) (*sql.Row, error) {
	query := "SELECT * FROM users WHERE email = '" + email + "'"
	return db.QueryRow(query), nil
}

// SAFE: Parameterized query
func SafeGetUser(db *sql.DB, userID int) (*sql.Row, error) {
	return db.QueryRow("SELECT * FROM users WHERE id = ?", userID), nil
}

// SAFE: Another parameterized query
func SafeSearchProducts(db *sql.DB, searchTerm string) (*sql.Rows, error) {
	return db.Query("SELECT * FROM products WHERE name LIKE ?", "%"+searchTerm+"%")
}

// SAFE: Parameterized update
func SafeUpdateEmail(db *sql.DB, userID int, email string) error {
	_, err := db.Exec("UPDATE users SET email = ? WHERE id = ?", email, userID)
	return err
}
