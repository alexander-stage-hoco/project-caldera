/// <summary>
/// C# file with light duplication - small duplicated blocks.
/// </summary>

using System;
using System.Collections.Generic;

namespace Synthetic.LightDuplication
{
    public class UserData
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
        public bool Active { get; set; } = true;
        public string CreatedAt { get; set; }
        public List<string> Permissions { get; set; }
    }

    public static class DataProcessor
    {
        public static UserData ProcessUserData(UserData user)
        {
            return new UserData
            {
                Id = user.Id,
                Name = (user.Name ?? "").Trim(),
                Email = (user.Email ?? "").ToLower().Trim(),
                Active = user.Active,
                CreatedAt = user.CreatedAt ?? ""
            };
        }

        public static UserData ProcessAdminData(UserData admin)
        {
            return new UserData
            {
                Id = admin.Id,
                Name = (admin.Name ?? "").Trim(),
                Email = (admin.Email ?? "").ToLower().Trim(),
                Active = admin.Active,
                CreatedAt = admin.CreatedAt ?? "",
                Permissions = admin.Permissions ?? new List<string>()
            };
        }

        public static bool ValidateEmail(string email)
        {
            if (string.IsNullOrEmpty(email)) return false;
            if (!email.Contains("@")) return false;
            var parts = email.Split('@');
            if (parts.Length != 2) return false;
            if (string.IsNullOrEmpty(parts[0]) || string.IsNullOrEmpty(parts[1])) return false;
            if (!parts[1].Contains(".")) return false;
            return true;
        }

        public static string FormatCurrency(decimal amount, string currency = "USD")
        {
            var symbols = new Dictionary<string, string>
            {
                { "USD", "$" },
                { "EUR", "E" },
                { "GBP", "P" }
            };
            var symbol = symbols.GetValueOrDefault(currency, currency);
            if (amount < 0)
            {
                return $"-{symbol}{Math.Abs(amount):N2}";
            }
            return $"{symbol}{amount:N2}";
        }

        public static decimal CalculateDiscount(decimal price, decimal discountPct)
        {
            if (discountPct < 0 || discountPct > 100)
            {
                throw new ArgumentException("Discount must be between 0 and 100");
            }
            return price * (1 - discountPct / 100);
        }
    }
}
