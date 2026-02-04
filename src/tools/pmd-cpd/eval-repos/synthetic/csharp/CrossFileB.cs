/// <summary>
/// C# file B for cross-file duplication - contains duplicate code from file A.
/// </summary>

using System;
using System.Collections.Generic;

namespace Synthetic.CrossFile
{
    public class InvoiceItem
    {
        public decimal Price { get; set; }
        public int Quantity { get; set; } = 1;
        public decimal Discount { get; set; }
        public string Name { get; set; }
    }

    public class Invoice
    {
        public string Id { get; set; }
        public string CustomerName { get; set; }
        public string Date { get; set; }
        public List<InvoiceItem> Items { get; set; }
        public decimal Subtotal { get; set; }
        public decimal Shipping { get; set; }
        public decimal Tax { get; set; }
        public decimal Total { get; set; }
    }

    public static class InvoiceCalculator
    {
        public static decimal CalculateInvoiceTotal(List<InvoiceItem> items)
        {
            decimal total = 0.0m;
            foreach (var item in items)
            {
                decimal price = item.Price;
                int quantity = item.Quantity;
                decimal discount = item.Discount;
                decimal itemTotal = price * quantity * (1 - discount / 100);
                total += itemTotal;
            }
            return Math.Round(total, 2);
        }

        private static readonly Dictionary<string, decimal> ShippingRates = new()
        {
            { "US", 5.99m },
            { "CA", 8.99m },
            { "UK", 12.99m },
            { "DE", 14.99m },
            { "FR", 14.99m },
            { "AU", 19.99m }
        };

        public static decimal ApplyDeliveryCost(decimal subtotal, string country)
        {
            decimal baseRate = ShippingRates.GetValueOrDefault(country, 24.99m);
            if (subtotal > 100) return subtotal;
            return subtotal + baseRate;
        }

        private static readonly Dictionary<string, decimal> TaxRates = new()
        {
            { "CA", 0.0725m },
            { "NY", 0.08m },
            { "TX", 0.0625m },
            { "FL", 0.06m },
            { "WA", 0.065m }
        };

        public static decimal ApplyVat(decimal subtotal, string state)
        {
            decimal rate = TaxRates.GetValueOrDefault(state, 0.0m);
            decimal tax = subtotal * rate;
            return Math.Round(subtotal + tax, 2);
        }

        public static string FormatInvoiceSummary(Invoice invoice)
        {
            var lines = new List<string>();
            lines.Add(new string('=', 50));
            lines.Add("INVOICE SUMMARY");
            lines.Add(new string('=', 50));
            lines.Add($"Invoice ID: {invoice.Id ?? "N/A"}");
            lines.Add($"Customer: {invoice.CustomerName ?? "Unknown"}");
            lines.Add($"Date: {invoice.Date ?? "Unknown"}");
            lines.Add(new string('-', 50));
            foreach (var item in invoice.Items ?? new List<InvoiceItem>())
            {
                lines.Add($"  {item.Name}: ${item.Price:F2}");
            }
            lines.Add(new string('-', 50));
            lines.Add($"Subtotal: ${invoice.Subtotal:F2}");
            lines.Add($"Shipping: ${invoice.Shipping:F2}");
            lines.Add($"Tax: ${invoice.Tax:F2}");
            lines.Add($"Total: ${invoice.Total:F2}");
            lines.Add(new string('=', 50));
            return string.Join("\n", lines);
        }
    }
}
