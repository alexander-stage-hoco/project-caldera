/**
 * Test file for DD smell D1_EMPTY_CATCH detection.
 * Contains multiple empty catch blocks.
 */

using System;
using System.IO;
using System.Text.Json;

namespace SmellTests.ErrorHandling
{
    public class EmptyCatchExamples
    {
        // D1_EMPTY_CATCH: Empty catch block
        public string ReadFileContent(string path)
        {
            try
            {
                return File.ReadAllText(path);
            }
            catch (FileNotFoundException)
            {
                // Empty catch - swallows exception
            }
            catch (IOException)
            {
                // Another empty catch
            }
            return string.Empty;
        }

        // D1_EMPTY_CATCH: Generic exception with empty body
        public T? ParseJson<T>(string json) where T : class
        {
            try
            {
                return JsonSerializer.Deserialize<T>(json);
            }
            catch (JsonException)
            {
                // Silently ignore JSON errors
            }
            return null;
        }

        // D1_EMPTY_CATCH: Multiple empty catches
        public void ProcessData(object data)
        {
            try
            {
                ValidateData(data);
                TransformData(data);
                SaveData(data);
            }
            catch (ArgumentNullException)
            {
            }
            catch (InvalidOperationException)
            {
            }
            catch (Exception)
            {
            }
        }

        // D1_EMPTY_CATCH in loop
        public void ProcessItems(string[] items)
        {
            foreach (var item in items)
            {
                try
                {
                    ProcessItem(item);
                }
                catch
                {
                    // Bare catch with empty body
                }
            }
        }

        private void ValidateData(object data) { }
        private void TransformData(object data) { }
        private void SaveData(object data) { }
        private void ProcessItem(string item) { }
    }
}
