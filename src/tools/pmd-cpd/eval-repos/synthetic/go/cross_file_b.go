// Package synthetic contains Go files for CPD testing - file B with duplicate code from A.
package synthetic

import (
	"fmt"
	"math"
	"strings"
)

// InvoiceItem represents an item in an invoice.
type InvoiceItem struct {
	Price    float64
	Quantity int
	Discount float64
	Name     string
}

// Invoice represents a complete invoice.
type Invoice struct {
	ID           string
	CustomerName string
	Date         string
	Items        []InvoiceItem
	Subtotal     float64
	Shipping     float64
	Tax          float64
	Total        float64
}

// CalculateInvoiceTotal calculates the total price of items - duplicate of order total.
func CalculateInvoiceTotal(items []InvoiceItem) float64 {
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

var deliveryRates = map[string]float64{
	"US": 5.99,
	"CA": 8.99,
	"UK": 12.99,
	"DE": 14.99,
	"FR": 14.99,
	"AU": 19.99,
}

// ApplyDeliveryCost applies delivery cost based on country - duplicate of shipping cost.
func ApplyDeliveryCost(subtotal float64, country string) float64 {
	baseRate, ok := deliveryRates[country]
	if !ok {
		baseRate = 24.99
	}
	if subtotal > 100 {
		return subtotal
	}
	return subtotal + baseRate
}

var vatRates = map[string]float64{
	"CA": 0.0725,
	"NY": 0.08,
	"TX": 0.0625,
	"FL": 0.06,
	"WA": 0.065,
}

// ApplyVat applies VAT based on state - duplicate of tax.
func ApplyVat(subtotal float64, state string) float64 {
	rate, ok := vatRates[state]
	if !ok {
		rate = 0.0
	}
	tax := subtotal * rate
	return math.Round((subtotal+tax)*100) / 100
}

// FormatInvoiceSummary formats the invoice summary for display - duplicate of order summary.
func FormatInvoiceSummary(invoice Invoice) string {
	var lines []string
	lines = append(lines, strings.Repeat("=", 50))
	lines = append(lines, "INVOICE SUMMARY")
	lines = append(lines, strings.Repeat("=", 50))
	id := invoice.ID
	if id == "" {
		id = "N/A"
	}
	customerName := invoice.CustomerName
	if customerName == "" {
		customerName = "Unknown"
	}
	date := invoice.Date
	if date == "" {
		date = "Unknown"
	}
	lines = append(lines, fmt.Sprintf("Invoice ID: %s", id))
	lines = append(lines, fmt.Sprintf("Customer: %s", customerName))
	lines = append(lines, fmt.Sprintf("Date: %s", date))
	lines = append(lines, strings.Repeat("-", 50))
	for _, item := range invoice.Items {
		lines = append(lines, fmt.Sprintf("  %s: $%.2f", item.Name, item.Price))
	}
	lines = append(lines, strings.Repeat("-", 50))
	lines = append(lines, fmt.Sprintf("Subtotal: $%.2f", invoice.Subtotal))
	lines = append(lines, fmt.Sprintf("Shipping: $%.2f", invoice.Shipping))
	lines = append(lines, fmt.Sprintf("Tax: $%.2f", invoice.Tax))
	lines = append(lines, fmt.Sprintf("Total: $%.2f", invoice.Total))
	lines = append(lines, strings.Repeat("=", 50))
	return strings.Join(lines, "\n")
}
