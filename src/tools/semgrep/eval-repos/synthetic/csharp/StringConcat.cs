// Test file for F4, F6: String concatenation and Event leaks
// Expected detections: 4 (F4 x2, F6 x2)

using System;
using System.Collections.Generic;
using System.Text;

namespace Synthetic.CSharp
{
    public class StringConcatAndEvents
    {
        // F6: Event subscription in constructor without cleanup
        public event EventHandler DataChanged;

        private readonly SomeService _service;

        // F6: Event subscription in constructor - high leak risk
        public StringConcatAndEvents(SomeService service)
        {
            _service = service;
            _service.Updated += OnServiceUpdated;  // Expected: DD-F6-EVENT-IN-CONSTRUCTOR-csharp
        }

        private void OnServiceUpdated(object sender, EventArgs e)
        {
            Console.WriteLine("Service updated");
        }

        // F4: String concatenation in for loop - BAD
        public string BuildListBad(IEnumerable<string> items)
        {
            string result = "";
            foreach (var item in items)
            {
                result = result + item + ", ";  // Expected: DD-F4-STRING-CONCAT-FOREACH-csharp
            }
            return result;
        }

        // F4: String concatenation with += in for loop - BAD
        public string BuildListBad2(string[] items)
        {
            string result = "";
            for (int i = 0; i < items.Length; i++)
            {
                result += items[i];  // Expected: DD-F4-STRING-PLUSEQUALS-csharp
            }
            return result;
        }

        // GOOD: Using StringBuilder
        public string BuildListGood(IEnumerable<string> items)
        {
            var sb = new StringBuilder();
            foreach (var item in items)
            {
                sb.Append(item).Append(", ");  // No detection - correct pattern
            }
            return sb.ToString();
        }

        // F6: Event subscription (general)
        public void Subscribe(SomeService service)
        {
            service.Updated += OnServiceUpdated;  // Expected: DD-F6-EVENT-SUBSCRIPTION-csharp
        }
    }

    public class SomeService
    {
        public event EventHandler Updated;

        public void TriggerUpdate()
        {
            Updated?.Invoke(this, EventArgs.Empty);
        }
    }
}
