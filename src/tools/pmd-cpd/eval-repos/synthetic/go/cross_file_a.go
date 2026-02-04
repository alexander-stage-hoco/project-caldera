// Package synthetic contains Go files for CPD testing - file A for cross-file detection.
package synthetic

import (
	"fmt"
	"math"
	"strings"
)

// OrderItem represents an item in an order.
type OrderItem struct {
	Price    float64
	Quantity int
	Discount float64
	Name     string
}

// Order represents a complete order.
type Order struct {
	ID           string
	CustomerName string
	Date         string
	Items        []OrderItem
	Subtotal     float64
	Shipping     float64
	Tax          float64
	Total        float64
}

// CalculateOrderTotal calculates the total price of items.
func CalculateOrderTotal(items []OrderItem) float64 {
	var total float64
	for _, item := range items {
		price := item.Price
		quantity := item.Quantity
		if quantity == 0 {
			quantity = 1
		}
		discount := item.Discount
		itemTotal := price * float64(quantity) * (1 - discount/100)
		total += itemTotal
	}
	return math.Round(total*100) / 100
}

var shippingRates = map[string]float64{
	"US": 5.99,
	"CA": 8.99,
	"UK": 12.99,
	"DE": 14.99,
	"FR": 14.99,
	"AU": 19.99,
}

// ApplyShippingCost applies shipping cost based on country.
func ApplyShippingCost(subtotal float64, country string) float64 {
	baseRate, ok := shippingRates[country]
	if !ok {
		baseRate = 24.99
	}
	if subtotal > 100 {
		return subtotal
	}
	return subtotal + baseRate
}

var taxRates = map[string]float64{
	"CA": 0.0725,
	"NY": 0.08,
	"TX": 0.0625,
	"FL": 0.06,
	"WA": 0.065,
}

// ApplyTax applies tax based on state.
func ApplyTax(subtotal float64, state string) float64 {
	rate, ok := taxRates[state]
	if !ok {
		rate = 0.0
	}
	tax := subtotal * rate
	return math.Round((subtotal+tax)*100) / 100
}

// FormatOrderSummary formats the order summary for display.
func FormatOrderSummary(order Order) string {
	var lines []string
	lines = append(lines, strings.Repeat("=", 50))
	lines = append(lines, "ORDER SUMMARY")
	lines = append(lines, strings.Repeat("=", 50))
	id := order.ID
	if id == "" {
		id = "N/A"
	}
	customerName := order.CustomerName
	if customerName == "" {
		customerName = "Unknown"
	}
	date := order.Date
	if date == "" {
		date = "Unknown"
	}
	lines = append(lines, fmt.Sprintf("Order ID: %s", id))
	lines = append(lines, fmt.Sprintf("Customer: %s", customerName))
	lines = append(lines, fmt.Sprintf("Date: %s", date))
	lines = append(lines, strings.Repeat("-", 50))
	for _, item := range order.Items {
		lines = append(lines, fmt.Sprintf("  %s: $%.2f", item.Name, item.Price))
	}
	lines = append(lines, strings.Repeat("-", 50))
	lines = append(lines, fmt.Sprintf("Subtotal: $%.2f", order.Subtotal))
	lines = append(lines, fmt.Sprintf("Shipping: $%.2f", order.Shipping))
	lines = append(lines, fmt.Sprintf("Tax: $%.2f", order.Tax))
	lines = append(lines, fmt.Sprintf("Total: $%.2f", order.Total))
	lines = append(lines, strings.Repeat("=", 50))
	return strings.Join(lines, "\n")
}
