// Package synthetic contains Go files for CPD testing with semantic duplicates (identifiers).
package synthetic

import (
	"math"
	"strings"
)

// ProfileData represents profile data.
type ProfileData struct {
	Age           int
	ActivityCount int
	PurchaseCount int
	ReferralCount int
	ID            int
	Name          string
	Email         string
	Active        bool
	CreatedAt     string
	LastSeen      string
}

// CalculateUserScore calculates score for a user based on profile data.
func CalculateUserScore(userData ProfileData) float64 {
	baseValue := 100.0
	userAge := userData.Age
	userActivity := userData.ActivityCount
	userPurchases := userData.PurchaseCount
	userReferrals := userData.ReferralCount

	if userAge > 18 {
		baseValue += 10.0
	}
	if userAge > 30 {
		baseValue += 5.0
	}
	if userActivity > 50 {
		baseValue += 20.0
	}
	if userPurchases > 10 {
		baseValue += 15.0
	}
	if userReferrals > 5 {
		baseValue += 25.0
	}

	return math.Min(baseValue, 200.0)
}

// CalculateCustomerRating calculates rating for a customer - semantic duplicate with renamed vars.
func CalculateCustomerRating(customerInfo ProfileData) float64 {
	startingScore := 100.0
	customerYears := customerInfo.Age
	customerInteractions := customerInfo.ActivityCount
	customerOrders := customerInfo.PurchaseCount
	customerInvites := customerInfo.ReferralCount

	if customerYears > 18 {
		startingScore += 10.0
	}
	if customerYears > 30 {
		startingScore += 5.0
	}
	if customerInteractions > 50 {
		startingScore += 20.0
	}
	if customerOrders > 10 {
		startingScore += 15.0
	}
	if customerInvites > 5 {
		startingScore += 25.0
	}

	return math.Min(startingScore, 200.0)
}

// ProcessedRecord represents a processed user record.
type ProcessedRecord struct {
	Identifier       int
	FullName         string
	EmailAddress     string
	IsActive         bool
	RegistrationDate string
	LastLogin        string
}

// ProcessedMember represents a processed member entry.
type ProcessedMember struct {
	MemberID       int
	DisplayName    string
	ContactEmail   string
	AccountStatus  bool
	SignupDate     string
	RecentActivity string
}

// ProcessUserRecord processes a user record with transformations.
func ProcessUserRecord(record ProfileData) ProcessedRecord {
	return ProcessedRecord{
		Identifier:       record.ID,
		FullName:         strings.TrimSpace(record.Name),
		EmailAddress:     strings.ToLower(strings.TrimSpace(record.Email)),
		IsActive:         record.Active,
		RegistrationDate: record.CreatedAt,
		LastLogin:        record.LastSeen,
	}
}

// ProcessMemberEntry processes a member entry - semantic duplicate with renamed vars.
func ProcessMemberEntry(entry ProfileData) ProcessedMember {
	return ProcessedMember{
		MemberID:       entry.ID,
		DisplayName:    strings.TrimSpace(entry.Name),
		ContactEmail:   strings.ToLower(strings.TrimSpace(entry.Email)),
		AccountStatus:  entry.Active,
		SignupDate:     entry.CreatedAt,
		RecentActivity: entry.LastSeen,
	}
}
