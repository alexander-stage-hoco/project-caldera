// Package synthetic contains Go files for CPD testing with semantic duplicates (literals).
package synthetic

import (
	"math"
	"regexp"
	"strings"
)

// CalculateBronzeTierDiscount calculates discount for bronze tier customers.
func CalculateBronzeTierDiscount(price float64) float64 {
	baseDiscount := 5.0
	maxDiscount := 15.0
	threshold := 100.0

	if price < threshold {
		return price * (1 - baseDiscount/100)
	}

	additional := (price - threshold) * 0.02
	totalDiscount := math.Min(baseDiscount+additional, maxDiscount)
	return price * (1 - totalDiscount/100)
}

// CalculateSilverTierDiscount calculates discount for silver tier - semantic duplicate with different literals.
func CalculateSilverTierDiscount(price float64) float64 {
	baseDiscount := 10.0
	maxDiscount := 25.0
	threshold := 150.0

	if price < threshold {
		return price * (1 - baseDiscount/100)
	}

	additional := (price - threshold) * 0.02
	totalDiscount := math.Min(baseDiscount+additional, maxDiscount)
	return price * (1 - totalDiscount/100)
}

// CalculateGoldTierDiscount calculates discount for gold tier - semantic duplicate with different literals.
func CalculateGoldTierDiscount(price float64) float64 {
	baseDiscount := 15.0
	maxDiscount := 35.0
	threshold := 200.0

	if price < threshold {
		return price * (1 - baseDiscount/100)
	}

	additional := (price - threshold) * 0.02
	totalDiscount := math.Min(baseDiscount+additional, maxDiscount)
	return price * (1 - totalDiscount/100)
}

// Address represents an address.
type Address struct {
	Street     string
	City       string
	State      string
	Zip        string
	Province   string
	PostalCode string
}

// ValidateUSAddress validates US address format.
func ValidateUSAddress(address Address) []string {
	var errors []string
	requiredFields := []string{"street", "city", "state", "zip"}
	statePattern := regexp.MustCompile(`^[A-Z]{2}$`)
	zipPattern := regexp.MustCompile(`^\d{5}(-\d{4})?$`)

	for _, field := range requiredFields {
		var value string
		switch field {
		case "street":
			value = address.Street
		case "city":
			value = address.City
		case "state":
			value = address.State
		case "zip":
			value = address.Zip
		}
		if value == "" {
			errors = append(errors, strings.Title(field)+" is required")
		}
	}

	if address.State != "" && !statePattern.MatchString(address.State) {
		errors = append(errors, "State must be 2 letter code")
	}
	if address.Zip != "" && !zipPattern.MatchString(address.Zip) {
		errors = append(errors, "ZIP must be 5 digits")
	}

	return errors
}

// ValidateCAAddress validates Canadian address - semantic duplicate with different literals.
func ValidateCAAddress(address Address) []string {
	var errors []string
	requiredFields := []string{"street", "city", "province", "postalCode"}
	provincePattern := regexp.MustCompile(`^[A-Z]{2}$`)
	postalPattern := regexp.MustCompile(`^[A-Z]\d[A-Z] ?\d[A-Z]\d$`)

	for _, field := range requiredFields {
		var value string
		switch field {
		case "street":
			value = address.Street
		case "city":
			value = address.City
		case "province":
			value = address.Province
		case "postalCode":
			value = address.PostalCode
		}
		if value == "" {
			errors = append(errors, strings.Title(field)+" is required")
		}
	}

	if address.Province != "" && !provincePattern.MatchString(address.Province) {
		errors = append(errors, "Province must be 2 letter code")
	}
	if address.PostalCode != "" && !postalPattern.MatchString(address.PostalCode) {
		errors = append(errors, "Postal code must be A1A 1A1 format")
	}

	return errors
}
