// Test file for B6: Message Chains (Law of Demeter violations)
// Expected detections: 2 (B6 x2)

using System;

namespace Synthetic.CSharp
{
    public class Company
    {
        public Department MainDepartment { get; set; }
    }

    public class Department
    {
        public Team LeadTeam { get; set; }
    }

    public class Team
    {
        public Manager TeamLead { get; set; }
    }

    public class Manager
    {
        public string Email { get; set; }
    }

    public class MessageChains
    {
        // B6: Long message chain - BAD
        public string GetManagerEmail(Company company)
        {
            // Expected: DD-B6-MESSAGE-CHAIN-csharp
            return company.MainDepartment.LeadTeam.TeamLead.Email;
        }

        // B6: Another long chain - BAD
        public void SendNotification(Company company)
        {
            // Expected: DD-B6-MESSAGE-CHAIN-csharp
            var email = company.MainDepartment.LeadTeam.TeamLead.Email;
            Console.WriteLine($"Sending to: {email}");
        }

        // GOOD: Short chain (not a smell)
        public string GetDepartmentName(Company company)
        {
            return company.MainDepartment.ToString();  // Only 2 levels - OK
        }
    }
}
