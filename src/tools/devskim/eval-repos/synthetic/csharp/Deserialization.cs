// Insecure Deserialization test cases for DevSkim evaluation
// Expected: DevSkim should detect insecure deserialization

using System;
using System.IO;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Formatters.Binary;
using System.Web.Script.Serialization;
using Newtonsoft.Json;

namespace SecurityTests
{
    public class Deserialization
    {
        // VULNERABLE: BinaryFormatter usage (DS113853)
        public object DeserializeWithBinaryFormatter(byte[] data)
        {
            using (var stream = new MemoryStream(data))
            {
                var formatter = new BinaryFormatter();
                return formatter.Deserialize(stream);
                // DevSkim should flag BinaryFormatter as insecure
            }
        }

        // VULNERABLE: TypeNameHandling.All (DS162963)
        public object DeserializeWithTypeNameHandling(string json)
        {
            var settings = new JsonSerializerSettings
            {
                TypeNameHandling = TypeNameHandling.All
            };
            return JsonConvert.DeserializeObject(json, settings);
            // DevSkim should flag TypeNameHandling.All
        }

        // VULNERABLE: TypeNameHandling.Auto
        public object DeserializeWithTypeNameAuto(string json)
        {
            var settings = new JsonSerializerSettings
            {
                TypeNameHandling = TypeNameHandling.Auto
            };
            return JsonConvert.DeserializeObject(json, settings);
            // DevSkim should flag TypeNameHandling.Auto
        }

        // VULNERABLE: JavaScriptSerializer with SimpleTypeResolver (DS172185)
        public object DeserializeWithJavaScriptSerializer(string json)
        {
            var serializer = new JavaScriptSerializer(new SimpleTypeResolver());
            return serializer.Deserialize<object>(json);
            // DevSkim should flag this
        }

        // VULNERABLE: NetDataContractSerializer
        public object DeserializeWithNetDataContract(Stream stream)
        {
            var serializer = new NetDataContractSerializer();
            return serializer.Deserialize(stream);
            // DevSkim should flag NetDataContractSerializer
        }

        // VULNERABLE: LosFormatter
        public object DeserializeWithLosFormatter(string data)
        {
            var formatter = new System.Web.UI.LosFormatter();
            return formatter.Deserialize(data);
            // DevSkim should flag LosFormatter
        }

        // SAFE: JSON.NET with default settings
        public T DeserializeSafe<T>(string json)
        {
            return JsonConvert.DeserializeObject<T>(json);
            // This should NOT be flagged (default is safe)
        }

        // SAFE: System.Text.Json (modern, type-safe)
        public T DeserializeWithSystemTextJson<T>(string json)
        {
            return System.Text.Json.JsonSerializer.Deserialize<T>(json);
            // This should NOT be flagged
        }

        // SAFE: DataContractSerializer with known types only
        public T DeserializeWithDataContract<T>(Stream stream)
        {
            var serializer = new DataContractSerializer(typeof(T));
            return (T)serializer.ReadObject(stream);
            // This should NOT be flagged (type-safe)
        }
    }
}
