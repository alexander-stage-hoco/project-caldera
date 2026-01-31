/**
 * Test file for DD smell E2_ASYNC_VOID detection.
 * Contains async void methods that are not event handlers.
 */

using System;
using System.Threading.Tasks;
using System.Net.Http;

namespace SmellTests.Async
{
    public class AsyncVoidExamples
    {
        // E2_ASYNC_VOID: Async void method - exceptions cannot be caught
        public async void ProcessUserAsync(int userId)
        {
            var user = await FetchUserAsync(userId);
            await SaveUserAsync(user);
        }

        // E2_ASYNC_VOID: Another async void method
        public async void SendNotificationAsync(string message)
        {
            await Task.Delay(100);
            Console.WriteLine(message);
        }

        // E2_ASYNC_VOID: Async void in service class
        public async void RefreshCacheAsync()
        {
            var data = await LoadDataAsync();
            UpdateCache(data);
        }

        // E2_ASYNC_VOID: Fire and forget pattern (bad)
        public async void LogAnalyticsAsync(string eventName, object data)
        {
            try
            {
                await SendToAnalyticsServerAsync(eventName, data);
            }
            catch (Exception)
            {
                // Exception will crash the process if not caught
            }
        }

        // CORRECT: Event handler - async void is acceptable here
        public async void OnButtonClick(object sender, EventArgs e)
        {
            await HandleClickAsync();
        }

        // CORRECT: Async Task method
        public async Task ProcessDataAsync(string data)
        {
            await Task.Delay(100);
            Console.WriteLine(data);
        }

        private Task<object> FetchUserAsync(int userId) => Task.FromResult<object>(new { Id = userId });
        private Task SaveUserAsync(object user) => Task.CompletedTask;
        private Task<object> LoadDataAsync() => Task.FromResult<object>(new { });
        private void UpdateCache(object data) { }
        private Task SendToAnalyticsServerAsync(string eventName, object data) => Task.CompletedTask;
        private Task HandleClickAsync() => Task.CompletedTask;
    }
}
