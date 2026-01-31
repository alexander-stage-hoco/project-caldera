using System;
using System.IO;
using System.Runtime.Serialization.Formatters.Binary;
using Newtonsoft.Json;

namespace SyntheticSmells.Security
{
    /// <summary>
    /// Insecure deserialization examples for Roslyn Analyzer testing.
    /// Demonstrates patterns that could lead to deserialization vulnerabilities.
    /// </summary>
    public class InsecureDeserializationExamples
    {
        // SYSLIB0011: BinaryFormatter is obsolete and insecure
        #pragma warning disable SYSLIB0011
        public object DeserializeWithBinaryFormatter(Stream stream)
        {
            var formatter = new BinaryFormatter();
            return formatter.Deserialize(stream);
        }

        public object DeserializeUntrustedData(byte[] data)
        {
            using var stream = new MemoryStream(data);
            var formatter = new BinaryFormatter();
            return formatter.Deserialize(stream);
        }
        #pragma warning restore SYSLIB0011

        // Vulnerable: TypeNameHandling.All allows arbitrary type instantiation
        public T DeserializeWithTypeHandlingAll<T>(string json)
        {
            var settings = new JsonSerializerSettings
            {
                TypeNameHandling = TypeNameHandling.All
            };
            return JsonConvert.DeserializeObject<T>(json, settings);
        }

        // Vulnerable: TypeNameHandling.Auto can still be exploited
        public T DeserializeWithTypeHandlingAuto<T>(string json)
        {
            var settings = new JsonSerializerSettings
            {
                TypeNameHandling = TypeNameHandling.Auto
            };
            return JsonConvert.DeserializeObject<T>(json, settings);
        }

        // SAFE: Using JSON with type handling disabled (no violation expected)
        public T SafeJsonDeserialize<T>(string json)
        {
            var settings = new JsonSerializerSettings
            {
                TypeNameHandling = TypeNameHandling.None
            };
            return JsonConvert.DeserializeObject<T>(json, settings);
        }

        // SAFE: Using System.Text.Json (no violation expected)
        public T SafeSystemTextJsonDeserialize<T>(string json)
        {
            return System.Text.Json.JsonSerializer.Deserialize<T>(json);
        }
    }
}
