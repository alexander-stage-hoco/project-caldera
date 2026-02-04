/// <summary>
/// C# file with semantic duplicates - same logic with different literal values.
/// </summary>

using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace Synthetic.SemanticLiterals
{
    public static class DiscountCalculator
    {
        public static double CalculateBronzeTierDiscount(double price)
        {
            double baseDiscount = 5.0;
            double maxDiscount = 15.0;
            double threshold = 100.0;

            if (price < threshold)
            {
                return price * (1 - baseDiscount / 100);
            }

            double additional = (price - threshold) * 0.02;
            double totalDiscount = Math.Min(baseDiscount + additional, maxDiscount);
            return price * (1 - totalDiscount / 100);
        }

        public static double CalculateSilverTierDiscount(double price)
        {
            double baseDiscount = 10.0;
            double maxDiscount = 25.0;
            double threshold = 150.0;

            if (price < threshold)
            {
                return price * (1 - baseDiscount / 100);
            }

            double additional = (price - threshold) * 0.02;
            double totalDiscount = Math.Min(baseDiscount + additional, maxDiscount);
            return price * (1 - totalDiscount / 100);
        }

        public static double CalculateGoldTierDiscount(double price)
        {
            double baseDiscount = 15.0;
            double maxDiscount = 35.0;
            double threshold = 200.0;

            if (price < threshold)
            {
                return price * (1 - baseDiscount / 100);
            }

            double additional = (price - threshold) * 0.02;
            double totalDiscount = Math.Min(baseDiscount + additional, maxDiscount);
            return price * (1 - totalDiscount / 100);
        }
    }

    public class Address
    {
        public string Street { get; set; }
        public string City { get; set; }
        public string State { get; set; }
        public string Zip { get; set; }
        public string Province { get; set; }
        public string PostalCode { get; set; }
    }

    public static class AddressValidator
    {
        public static List<string> ValidateUsAddress(Address address)
        {
            var errors = new List<string>();
            var requiredFields = new[] { "street", "city", "state", "zip" };
            var statePattern = new Regex(@"^[A-Z]{2}$");
            var zipPattern = new Regex(@"^\d{5}(-\d{4})?$");

            foreach (var field in requiredFields)
            {
                var value = field switch
                {
                    "street" => address.Street,
                    "city" => address.City,
                    "state" => address.State,
                    "zip" => address.Zip,
                    _ => null
                };
                if (string.IsNullOrEmpty(value))
                {
                    errors.Add($"{char.ToUpper(field[0]) + field.Substring(1)} is required");
                }
            }

            if (!string.IsNullOrEmpty(address.State) && !statePattern.IsMatch(address.State))
            {
                errors.Add("State must be 2 letter code");
            }
            if (!string.IsNullOrEmpty(address.Zip) && !zipPattern.IsMatch(address.Zip))
            {
                errors.Add("ZIP must be 5 digits");
            }

            return errors;
        }

        public static List<string> ValidateCaAddress(Address address)
        {
            var errors = new List<string>();
            var requiredFields = new[] { "street", "city", "province", "postalCode" };
            var provincePattern = new Regex(@"^[A-Z]{2}$");
            var postalPattern = new Regex(@"^[A-Z]\d[A-Z] ?\d[A-Z]\d$");

            foreach (var field in requiredFields)
            {
                var value = field switch
                {
                    "street" => address.Street,
                    "city" => address.City,
                    "province" => address.Province,
                    "postalCode" => address.PostalCode,
                    _ => null
                };
                if (string.IsNullOrEmpty(value))
                {
                    errors.Add($"{char.ToUpper(field[0]) + field.Substring(1)} is required");
                }
            }

            if (!string.IsNullOrEmpty(address.Province) && !provincePattern.IsMatch(address.Province))
            {
                errors.Add("Province must be 2 letter code");
            }
            if (!string.IsNullOrEmpty(address.PostalCode) && !postalPattern.IsMatch(address.PostalCode))
            {
                errors.Add("Postal code must be A1A 1A1 format");
            }

            return errors;
        }
    }
}
