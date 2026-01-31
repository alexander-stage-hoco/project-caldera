using System;
using System.Collections.Generic;

namespace SyntheticSmells.Design
{
    /// <summary>
    /// God class examples for Roslyn Analyzer testing.
    /// Expected violations: CA1502 (2 - excessive complexity), CA1506 (2 - excessive coupling) = 4 total
    /// </summary>

    // CA1502/CA1506: God class with too many responsibilities (line 12)
    public class GodClassManager
    {
        // Excessive dependencies (coupling)
        private readonly UserService _userService = new();
        private readonly OrderService _orderService = new();
        private readonly ProductService _productService = new();
        private readonly PaymentService _paymentService = new();
        private readonly ShippingService _shippingService = new();
        private readonly NotificationService _notificationService = new();
        private readonly ReportingService _reportingService = new();
        private readonly AnalyticsService _analyticsService = new();
        private readonly CacheService _cacheService = new();
        private readonly LoggingService _loggingService = new();
        private readonly ConfigService _configService = new();
        private readonly SecurityService _securityService = new();

        // CA1502: Method with excessive cyclomatic complexity (>25 branches)
        public string ProcessOrder(int orderId, string status, int priority, bool urgent, bool express, string region)
        {
            // CCN = 40+ due to nested conditionals
            if (orderId <= 0) return "invalid_id";
            if (string.IsNullOrEmpty(status)) return "invalid_status";
            if (priority < 0) return "invalid_priority";
            if (priority > 10) return "priority_overflow";

            switch (status)
            {
                case "new":
                    if (priority > 8) return urgent && express ? "super_rush_new" : urgent ? "rush_new" : express ? "fast_new" : "high_new";
                    else if (priority > 5) return urgent ? "high_new" : "normal_new";
                    else if (priority > 3) return express ? "express_new" : "standard_new";
                    else return region == "US" ? "us_new" : region == "EU" ? "eu_new" : region == "APAC" ? "apac_new" : "intl_new";
                case "pending":
                    if (urgent && express) return priority > 5 ? "ultra_rush_pending" : "rush_pending";
                    else if (urgent) return priority > 7 ? "critical_pending" : "urgent_pending";
                    else if (express) return region == "US" ? "us_express_pending" : "express_pending";
                    else return priority > 3 ? "priority_pending" : region == "EU" ? "eu_pending" : "standard_pending";
                case "processing":
                    if (priority > 8) return urgent && express ? "critical_rush_proc" : urgent ? "critical_proc" : "high_proc";
                    else if (priority > 7) return urgent ? "critical_proc" : express ? "fast_proc" : "high_proc";
                    else if (priority > 4) return region == "US" ? "us_proc" : region == "EU" ? "eu_proc" : "other_proc";
                    else return urgent ? "low_urgent_proc" : "normal_proc";
                case "shipped":
                    if (region == "US") return urgent ? "us_rush_shipped" : express ? "us_express_shipped" : "us_shipped";
                    else if (region == "EU") return urgent ? "eu_rush_shipped" : express ? "eu_express_shipped" : "eu_shipped";
                    else return urgent ? "rush_shipped" : express ? "express_shipped" : "standard_shipped";
                case "delivered":
                    if (region == "US") return urgent && express ? "us_super_delivered" : urgent ? "us_rush_delivered" : express ? "us_express_delivered" : "us_delivered";
                    else if (region == "EU") return urgent && express ? "eu_super_delivered" : urgent ? "eu_rush_delivered" : express ? "eu_express_delivered" : "eu_delivered";
                    else if (region == "APAC") return urgent ? "apac_rush_delivered" : express ? "apac_express_delivered" : "apac_delivered";
                    else return urgent ? "intl_rush_delivered" : express ? "intl_express_delivered" : "intl_delivered";
                case "cancelled":
                    if (priority > 5) return urgent ? "high_cancelled" : "priority_cancelled";
                    else return region == "US" ? "us_cancelled" : "cancelled";
                case "refunded":
                    return urgent && express ? "rush_refunded" : urgent ? "urgent_refunded" : express ? "express_refunded" : priority > 5 ? "priority_refunded" : "standard_refunded";
                default:
                    if (priority > 7) return urgent ? "unknown_critical" : "unknown_high";
                    else if (priority > 5) return express ? "unknown_fast" : "unknown_med_high";
                    else if (priority > 2) return "unknown_med";
                    else return region == "US" ? "unknown_us_low" : "unknown_low";
            }
        }

        // CA1502: Another high complexity method
        public int CalculateShippingCost(string region, string method, double weight, bool insured, bool signature, bool fragile, int priority)
        {
            // CCN = 35+ branches
            if (weight <= 0) return -1;
            if (string.IsNullOrEmpty(region)) return -2;
            if (string.IsNullOrEmpty(method)) return -3;

            int baseCost = 0;
            switch (method)
            {
                case "ground":
                    baseCost = weight < 1 ? 5 : weight < 5 ? 10 : weight < 10 ? 15 : weight < 25 ? 25 : 40;
                    break;
                case "express":
                    baseCost = weight < 1 ? 15 : weight < 5 ? 25 : weight < 10 ? 40 : weight < 25 ? 60 : 100;
                    break;
                case "overnight":
                    baseCost = weight < 1 ? 30 : weight < 5 ? 50 : weight < 10 ? 80 : weight < 25 ? 120 : 200;
                    break;
                case "freight":
                    baseCost = weight < 50 ? 50 : weight < 100 ? 100 : weight < 500 ? 250 : 500;
                    break;
                default:
                    baseCost = 20;
                    break;
            }

            // Region adjustments
            if (region == "US") baseCost = (int)(baseCost * 1.0);
            else if (region == "CA") baseCost = (int)(baseCost * 1.2);
            else if (region == "EU") baseCost = (int)(baseCost * 1.5);
            else if (region == "UK") baseCost = (int)(baseCost * 1.4);
            else if (region == "APAC") baseCost = (int)(baseCost * 1.8);
            else if (region == "LATAM") baseCost = (int)(baseCost * 1.6);
            else baseCost = (int)(baseCost * 2.0);

            // Priority adjustments
            if (priority > 8) baseCost = (int)(baseCost * 2.0);
            else if (priority > 6) baseCost = (int)(baseCost * 1.5);
            else if (priority > 4) baseCost = (int)(baseCost * 1.2);

            // Options
            if (insured && fragile) baseCost += 50;
            else if (insured) baseCost += 25;
            else if (fragile) baseCost += 15;

            if (signature) baseCost += priority > 5 ? 10 : 5;

            return baseCost;
        }

        public void CancelOrder(int orderId) { }
        public void RefundOrder(int orderId) { }
        public void UpdateOrderStatus(int orderId, string status) { }
        public void SendOrderNotification(int orderId) { }
        public void GenerateOrderReport(int orderId) { }
        public void TrackOrderShipment(int orderId) { }
        public void CalculateOrderTax(int orderId) { }
        public void ApplyOrderDiscount(int orderId, decimal discount) { }
        public void ValidateOrderInventory(int orderId) { }
        public void ProcessOrderPayment(int orderId) { }
        public void ArchiveCompletedOrder(int orderId) { }
        public void ExportOrderData(int orderId) { }
        public void ImportOrderData(string data) { }
        public void SyncOrderWithExternalSystem(int orderId) { }
        public void AuditOrderChanges(int orderId) { }
        public void HandleOrderException(int orderId, Exception ex) { }
        public void ReprocessFailedOrder(int orderId) { }
        public void BatchProcessOrders(List<int> orderIds) { }
        public void ScheduleOrderProcessing(int orderId, DateTime time) { }
        public void ClearOrderCache(int orderId) { }
        public void UpdateOrderMetrics(int orderId) { }
        public void NotifyOrderStakeholders(int orderId) { }
        public void GenerateOrderInvoice(int orderId) { }
        public void SendOrderToWarehouse(int orderId) { }
    }

    // CA1502/CA1506: Another god class with mixed responsibilities (line 60)
    public class ApplicationController
    {
        // Dependencies showing high coupling
        private readonly Database _database = new();
        private readonly EmailService _email = new();
        private readonly SmsService _sms = new();
        private readonly FileStorage _storage = new();
        private readonly QueueService _queue = new();
        private readonly CronService _cron = new();
        private readonly MetricsService _metrics = new();
        private readonly HealthCheckService _health = new();
        private readonly AuthenticationService _auth = new();
        private readonly AuthorizationService _authz = new();

        // Mixed responsibilities
        public void Initialize() { }
        public void Shutdown() { }
        public void HandleRequest(object request) { }
        public void ProcessBackground() { }
        public void SendEmail(string to, string subject, string body) { }
        public void SendSms(string number, string message) { }
        public void SaveFile(string path, byte[] data) { }
        public void LoadFile(string path) { }
        public void QueueJob(object job) { }
        public void ProcessQueue() { }
        public void ScheduleTask(string name, Action task) { }
        public void CancelTask(string name) { }
        public void RecordMetric(string name, double value) { }
        public void CheckHealth() { }
        public bool Authenticate(string user, string pass) { return true; }
        public bool Authorize(string user, string action) { return true; }
        public void LogActivity(string activity) { }
        public void ClearCache() { }
        public void BackupDatabase() { }
        public void RestoreDatabase(string backup) { }
    }

    // Helper service stubs for coupling demonstration
    public class UserService { }
    public class OrderService { }
    public class ProductService { }
    public class PaymentService { }
    public class ShippingService { }
    public class NotificationService { }
    public class ReportingService { }
    public class AnalyticsService { }
    public class CacheService { }
    public class LoggingService { }
    public class ConfigService { }
    public class SecurityService { }
    public class Database { }
    public class EmailService { }
    public class SmsService { }
    public class FileStorage { }
    public class QueueService { }
    public class CronService { }
    public class MetricsService { }
    public class HealthCheckService { }
    public class AuthenticationService { }
    public class AuthorizationService { }
}
