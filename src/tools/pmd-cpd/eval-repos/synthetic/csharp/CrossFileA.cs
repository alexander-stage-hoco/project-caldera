/// <summary>
/// C# file A for cross-file duplication detection.
/// </summary>

using System;
using System.Collections.Generic;

namespace Synthetic.CrossFile
{
    public class OrderItem
    {
        public decimal Price { get; set; }
        public int Quantity { get; set; } = 1;
        public decimal Discount { get; set; }
        public string Name { get; set; }
    }

    public class Order
    {
        public string Id { get; set; }
        public string CustomerName { get; set; }
        public string Date { get; set; }
        public List<OrderItem> Items { get; set; }
        public decimal Subtotal { get; set; }
        public decimal Shipping { get; set; }
        public decimal Tax { get; set; }
        public decimal Total { get; set; }
    }

    public static class OrderCalculator
    {
        public static decimal CalculateOrderTotal(List<OrderItem> items)
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

        public static decimal ApplyShippingCost(decimal subtotal, string country)
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

        public static decimal ApplyTax(decimal subtotal, string state)
        {
            decimal rate = TaxRates.GetValueOrDefault(state, 0.0m);
            decimal tax = subtotal * rate;
            return Math.Round(subtotal + tax, 2);
        }

        public static string FormatOrderSummary(Order order)
        {
            var lines = new List<string>();
            lines.Add(new string('=', 50));
            lines.Add("ORDER SUMMARY");
            lines.Add(new string('=', 50));
            lines.Add($"Order ID: {order.Id ?? "N/A"}");
            lines.Add($"Customer: {order.CustomerName ?? "Unknown"}");
            lines.Add($"Date: {order.Date ?? "Unknown"}");
            lines.Add(new string('-', 50));
            foreach (var item in order.Items ?? new List<OrderItem>())
            {
                lines.Add($"  {item.Name}: ${item.Price:F2}");
            }
            lines.Add(new string('-', 50));
            lines.Add($"Subtotal: ${order.Subtotal:F2}");
            lines.Add($"Shipping: ${order.Shipping:F2}");
            lines.Add($"Tax: ${order.Tax:F2}");
            lines.Add($"Total: ${order.Total:F2}");
            lines.Add(new string('=', 50));
            return string.Join("\n", lines);
        }
    }
}
