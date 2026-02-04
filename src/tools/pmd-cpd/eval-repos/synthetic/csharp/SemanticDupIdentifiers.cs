/// <summary>
/// C# file with semantic duplicates - same logic with different variable names.
/// </summary>

using System;

namespace Synthetic.SemanticDuplicates
{
    public class ProfileData
    {
        public int Age { get; set; }
        public int ActivityCount { get; set; }
        public int PurchaseCount { get; set; }
        public int ReferralCount { get; set; }
        public int Id { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
        public bool Active { get; set; }
        public string CreatedAt { get; set; }
        public string LastSeen { get; set; }
    }

    public static class ScoreCalculator
    {
        public static double CalculateUserScore(ProfileData userData)
        {
            double baseValue = 100.0;
            int userAge = userData.Age;
            int userActivity = userData.ActivityCount;
            int userPurchases = userData.PurchaseCount;
            int userReferrals = userData.ReferralCount;

            if (userAge > 18) baseValue += 10.0;
            if (userAge > 30) baseValue += 5.0;
            if (userActivity > 50) baseValue += 20.0;
            if (userPurchases > 10) baseValue += 15.0;
            if (userReferrals > 5) baseValue += 25.0;

            return Math.Min(baseValue, 200.0);
        }

        public static double CalculateCustomerRating(ProfileData customerInfo)
        {
            double startingScore = 100.0;
            int customerYears = customerInfo.Age;
            int customerInteractions = customerInfo.ActivityCount;
            int customerOrders = customerInfo.PurchaseCount;
            int customerInvites = customerInfo.ReferralCount;

            if (customerYears > 18) startingScore += 10.0;
            if (customerYears > 30) startingScore += 5.0;
            if (customerInteractions > 50) startingScore += 20.0;
            if (customerOrders > 10) startingScore += 15.0;
            if (customerInvites > 5) startingScore += 25.0;

            return Math.Min(startingScore, 200.0);
        }
    }

    public class ProcessedRecord
    {
        public int Identifier { get; set; }
        public string FullName { get; set; }
        public string EmailAddress { get; set; }
        public bool IsActive { get; set; }
        public string RegistrationDate { get; set; }
        public string LastLogin { get; set; }
    }

    public class ProcessedMember
    {
        public int MemberId { get; set; }
        public string DisplayName { get; set; }
        public string ContactEmail { get; set; }
        public bool AccountStatus { get; set; }
        public string SignupDate { get; set; }
        public string RecentActivity { get; set; }
    }

    public static class RecordProcessor
    {
        public static ProcessedRecord ProcessUserRecord(ProfileData record)
        {
            return new ProcessedRecord
            {
                Identifier = record.Id,
                FullName = (record.Name ?? "").Trim(),
                EmailAddress = (record.Email ?? "").ToLower().Trim(),
                IsActive = record.Active,
                RegistrationDate = record.CreatedAt ?? "",
                LastLogin = record.LastSeen ?? ""
            };
        }

        public static ProcessedMember ProcessMemberEntry(ProfileData entry)
        {
            return new ProcessedMember
            {
                MemberId = entry.Id,
                DisplayName = (entry.Name ?? "").Trim(),
                ContactEmail = (entry.Email ?? "").ToLower().Trim(),
                AccountStatus = entry.Active,
                SignupDate = entry.CreatedAt ?? "",
                RecentActivity = entry.LastSeen ?? ""
            };
        }
    }
}
