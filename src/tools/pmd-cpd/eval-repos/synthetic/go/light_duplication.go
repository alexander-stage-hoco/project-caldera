// Package synthetic contains Go files for CPD testing with light duplication.
package synthetic

import (
	"errors"
	"fmt"
	"strings"
)

// UserData represents user data.
type UserData struct {
	ID          int
	Name        string
	Email       string
	Active      bool
	CreatedAt   string
	Permissions []string
}

// ProcessUserData processes user data with validation.
func ProcessUserData(user UserData) UserData {
	return UserData{
		ID:        user.ID,
		Name:      strings.TrimSpace(user.Name),
		Email:     strings.ToLower(strings.TrimSpace(user.Email)),
		Active:    user.Active,
		CreatedAt: user.CreatedAt,
	}
}

// ProcessAdminData processes admin data with validation - light duplication.
func ProcessAdminData(admin UserData) UserData {
	return UserData{
		ID:          admin.ID,
		Name:        strings.TrimSpace(admin.Name),
		Email:       strings.ToLower(strings.TrimSpace(admin.Email)),
		Active:      admin.Active,
		CreatedAt:   admin.CreatedAt,
		Permissions: admin.Permissions,
	}
}

// ValidateEmail validates email format.
func ValidateEmail(email string) bool {
	if email == "" {
		return false
	}
	if !strings.Contains(email, "@") {
		return false
	}
	parts := strings.Split(email, "@")
	if len(parts) != 2 {
		return false
	}
	if parts[0] == "" || parts[1] == "" {
		return false
	}
	if !strings.Contains(parts[1], ".") {
		return false
	}
	return true
}

// FormatCurrency formats a number as currency.
func FormatCurrency(amount float64, currency string) string {
	symbols := map[string]string{
		"USD": "$",
		"EUR": "E",
		"GBP": "P",
	}
	symbol, ok := symbols[currency]
	if !ok {
		symbol = currency
	}
	if amount < 0 {
		return fmt.Sprintf("-%s%.2f", symbol, -amount)
	}
	return fmt.Sprintf("%s%.2f", symbol, amount)
}

// CalculateDiscount calculates discounted price.
func CalculateDiscount(price, discountPct float64) (float64, error) {
	if discountPct < 0 || discountPct > 100 {
		return 0, errors.New("discount must be between 0 and 100")
	}
	return price * (1 - discountPct/100), nil
}
