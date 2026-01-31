/**
 * Test file for Unsafe Deserialization vulnerability detection.
 * Contains insecure deserialization patterns for C#.
 */

using System;
using System.IO;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Formatters.Binary;
using System.Runtime.Serialization.Formatters.Soap;
using System.Runtime.Serialization.Json;
using System.Web.Script.Serialization;
using System.Xml.Serialization;
using Newtonsoft.Json;

namespace SmellTests.Security
{
    public class DeserializationRiskExamples
    {
        // UNSAFE_DESERIALIZATION: BinaryFormatter is dangerous
        public object DeserializeWithBinaryFormatter(byte[] data)
        {
            // BAD: BinaryFormatter can execute arbitrary code
            using var stream = new MemoryStream(data);
            var formatter = new BinaryFormatter();
            return formatter.Deserialize(stream);  // Extremely dangerous!
        }

        // UNSAFE_DESERIALIZATION: BinaryFormatter.Deserialize from file
        public T LoadObjectFromFile<T>(string filePath)
        {
            // BAD: BinaryFormatter from untrusted source
            using var stream = File.OpenRead(filePath);
            var formatter = new BinaryFormatter();
            return (T)formatter.Deserialize(stream);
        }

        // UNSAFE_DESERIALIZATION: SoapFormatter (also dangerous)
        public object DeserializeWithSoapFormatter(Stream stream)
        {
            // BAD: SoapFormatter has similar risks to BinaryFormatter
            var formatter = new SoapFormatter();
            return formatter.Deserialize(stream);
        }

        // UNSAFE_DESERIALIZATION: NetDataContractSerializer
        public object DeserializeWithNetDataContract(Stream stream)
        {
            // BAD: NetDataContractSerializer can deserialize any type
            var serializer = new NetDataContractSerializer();
            return serializer.Deserialize(stream);
        }

        // UNSAFE_DESERIALIZATION: LosFormatter
        public object DeserializeWithLosFormatter(string data)
        {
            // BAD: LosFormatter is vulnerable
            var formatter = new System.Web.UI.LosFormatter();
            return formatter.Deserialize(data);
        }

        // UNSAFE_DESERIALIZATION: ObjectStateFormatter
        public object DeserializeWithObjectStateFormatter(string data)
        {
            // BAD: ObjectStateFormatter can be exploited
            var formatter = new System.Web.UI.ObjectStateFormatter();
            return formatter.Deserialize(data);
        }

        // UNSAFE_DESERIALIZATION: JavaScriptSerializer with type resolvers
        public object DeserializeWithJavaScript(string json)
        {
            // BAD: JavaScriptSerializer with SimpleTypeResolver
            var serializer = new JavaScriptSerializer(new SimpleTypeResolver());
            return serializer.DeserializeObject(json);
        }

        // UNSAFE_DESERIALIZATION: Newtonsoft JSON with TypeNameHandling
        public T DeserializeWithNewtonsoft<T>(string json)
        {
            // BAD: TypeNameHandling.All allows arbitrary type instantiation
            var settings = new JsonSerializerSettings
            {
                TypeNameHandling = TypeNameHandling.All  // Dangerous!
            };
            return JsonConvert.DeserializeObject<T>(json, settings);
        }

        // UNSAFE_DESERIALIZATION: TypeNameHandling.Auto can also be dangerous
        public T DeserializeWithAutoType<T>(string json)
        {
            // BAD: TypeNameHandling.Auto can be exploited
            var settings = new JsonSerializerSettings
            {
                TypeNameHandling = TypeNameHandling.Auto
            };
            return JsonConvert.DeserializeObject<T>(json, settings);
        }

        // UNSAFE_DESERIALIZATION: TypeNameHandling.Objects
        public object DeserializeWithObjectsType(string json)
        {
            // BAD: TypeNameHandling.Objects is also risky
            var settings = new JsonSerializerSettings
            {
                TypeNameHandling = TypeNameHandling.Objects
            };
            return JsonConvert.DeserializeObject(json, settings);
        }

        // UNSAFE_DESERIALIZATION: DataContractSerializer with known types from input
        public object DeserializeWithDataContract(Stream stream, Type type)
        {
            // BAD: Type comes from untrusted source
            var serializer = new DataContractSerializer(type);
            return serializer.ReadObject(stream);
        }

        // UNSAFE_DESERIALIZATION: XmlSerializer with user-controlled type
        public object DeserializeXml(string xml, string typeName)
        {
            // BAD: Type name from user input
            var type = Type.GetType(typeName);  // Type from user!
            var serializer = new XmlSerializer(type);
            using var reader = new StringReader(xml);
            return serializer.Deserialize(reader);
        }

        // CORRECT: System.Text.Json (safe by default)
        public T DeserializeSafe<T>(string json)
        {
            // GOOD: System.Text.Json is safe by default
            return System.Text.Json.JsonSerializer.Deserialize<T>(json);
        }

        // CORRECT: Newtonsoft without TypeNameHandling
        public T DeserializeNewtonsoftSafe<T>(string json)
        {
            // GOOD: No TypeNameHandling (or TypeNameHandling.None)
            var settings = new JsonSerializerSettings
            {
                TypeNameHandling = TypeNameHandling.None
            };
            return JsonConvert.DeserializeObject<T>(json, settings);
        }

        // CORRECT: DataContractSerializer with known type
        public MyDataClass DeserializeKnownType(Stream stream)
        {
            // GOOD: Using specific known type
            var serializer = new DataContractSerializer(typeof(MyDataClass));
            return (MyDataClass)serializer.ReadObject(stream);
        }

        // CORRECT: Using a SerializationBinder to restrict types
        public T DeserializeWithBinder<T>(string json)
        {
            // GOOD: Custom binder restricts allowed types
            var settings = new JsonSerializerSettings
            {
                TypeNameHandling = TypeNameHandling.Objects,
                SerializationBinder = new SafeSerializationBinder()
            };
            return JsonConvert.DeserializeObject<T>(json, settings);
        }
    }

    [DataContract]
    public class MyDataClass
    {
        [DataMember]
        public string Name { get; set; }
    }

    // Custom binder for safe deserialization
    public class SafeSerializationBinder : ISerializationBinder
    {
        private static readonly Type[] AllowedTypes = { typeof(MyDataClass) };

        public Type BindToType(string assemblyName, string typeName)
        {
            foreach (var type in AllowedTypes)
            {
                if (type.FullName == typeName)
                    return type;
            }
            throw new JsonSerializationException($"Type {typeName} is not allowed");
        }

        public void BindToName(Type serializedType, out string assemblyName, out string typeName)
        {
            assemblyName = null;
            typeName = serializedType.FullName;
        }
    }
}
