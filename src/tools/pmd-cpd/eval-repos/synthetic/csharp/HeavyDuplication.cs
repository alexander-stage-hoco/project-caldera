/// <summary>
/// C# file with heavy duplication - multiple large duplicated blocks.
/// </summary>

using System;
using System.Collections.Generic;
using System.Text;

namespace Synthetic.HeavyDuplication
{
    public class ReportItem
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
        public string Status { get; set; }
        public string CreatedAt { get; set; }
    }

    public static class ReportGenerator
    {
        public static string GenerateUserReport(List<ReportItem> users)
        {
            var lines = new List<string>();
            lines.Add(new string('=', 60));
            lines.Add("USER REPORT");
            lines.Add(new string('=', 60));
            lines.Add("");

            foreach (var item in users)
            {
                lines.Add($"ID: {item.Id ?? "N/A"}");
                lines.Add($"Name: {item.Name ?? "Unknown"}");
                lines.Add($"Email: {item.Email ?? "N/A"}");
                lines.Add($"Status: {item.Status ?? "active"}");
                lines.Add($"Created: {item.CreatedAt ?? "Unknown"}");
                lines.Add(new string('-', 40));
            }

            lines.Add("");
            lines.Add($"Total records: {users.Count}");
            lines.Add(new string('=', 60));
            return string.Join("\n", lines);
        }

        public static string GenerateAdminReport(List<ReportItem> admins)
        {
            var lines = new List<string>();
            lines.Add(new string('=', 60));
            lines.Add("ADMIN REPORT");
            lines.Add(new string('=', 60));
            lines.Add("");

            foreach (var item in admins)
            {
                lines.Add($"ID: {item.Id ?? "N/A"}");
                lines.Add($"Name: {item.Name ?? "Unknown"}");
                lines.Add($"Email: {item.Email ?? "N/A"}");
                lines.Add($"Status: {item.Status ?? "active"}");
                lines.Add($"Created: {item.CreatedAt ?? "Unknown"}");
                lines.Add(new string('-', 40));
            }

            lines.Add("");
            lines.Add($"Total records: {admins.Count}");
            lines.Add(new string('=', 60));
            return string.Join("\n", lines);
        }

        public static string GenerateGuestReport(List<ReportItem> guests)
        {
            var lines = new List<string>();
            lines.Add(new string('=', 60));
            lines.Add("GUEST REPORT");
            lines.Add(new string('=', 60));
            lines.Add("");

            foreach (var item in guests)
            {
                lines.Add($"ID: {item.Id ?? "N/A"}");
                lines.Add($"Name: {item.Name ?? "Unknown"}");
                lines.Add($"Email: {item.Email ?? "N/A"}");
                lines.Add($"Status: {item.Status ?? "active"}");
                lines.Add($"Created: {item.CreatedAt ?? "Unknown"}");
                lines.Add(new string('-', 40));
            }

            lines.Add("");
            lines.Add($"Total records: {guests.Count}");
            lines.Add(new string('=', 60));
            return string.Join("\n", lines);
        }
    }

    public class InputData
    {
        public string Name { get; set; }
        public string Email { get; set; }
        public string Password { get; set; }
        public int? Age { get; set; }
    }

    public static class Validator
    {
        public static List<string> ValidateUserInput(InputData data)
        {
            var errors = new List<string>();
            if (string.IsNullOrEmpty(data.Name)) errors.Add("Name is required");
            if (string.IsNullOrEmpty(data.Email)) errors.Add("Email is required");
            if (data.Email?.Contains("@") != true) errors.Add("Invalid email format");
            if (string.IsNullOrEmpty(data.Password)) errors.Add("Password is required");
            if ((data.Password ?? "").Length < 8) errors.Add("Password must be at least 8 characters");
            if (!data.Age.HasValue) errors.Add("Age is required");
            if ((data.Age ?? 0) < 18) errors.Add("Must be at least 18 years old");
            return errors;
        }

        public static List<string> ValidateAdminInput(InputData data)
        {
            var errors = new List<string>();
            if (string.IsNullOrEmpty(data.Name)) errors.Add("Name is required");
            if (string.IsNullOrEmpty(data.Email)) errors.Add("Email is required");
            if (data.Email?.Contains("@") != true) errors.Add("Invalid email format");
            if (string.IsNullOrEmpty(data.Password)) errors.Add("Password is required");
            if ((data.Password ?? "").Length < 8) errors.Add("Password must be at least 8 characters");
            if (!data.Age.HasValue) errors.Add("Age is required");
            if ((data.Age ?? 0) < 18) errors.Add("Must be at least 18 years old");
            return errors;
        }
    }
}
