using System;
using System.IO;
using System.Net.Http;

namespace ResourceManagement.Dispose
{
    /// <summary>
    /// Missing dispose/using violations.
    /// Expected violations: CA2000 (Dispose objects before losing scope)
    /// </summary>
    public class MissingDisposeExamples
    {
        // CA2000: Object not disposed before losing scope
        public string ReadFileContent(string path)
        {
            var reader = new StreamReader(path);  // CA2000
            return reader.ReadToEnd();
            // reader is never disposed
        }

        // CA2000: FileStream not disposed
        public void WriteToFile(string path, string content)
        {
            var stream = new FileStream(path, FileMode.Create);  // CA2000
            var writer = new StreamWriter(stream);  // CA2000
            writer.Write(content);
            // Neither stream nor writer is disposed
        }

        // CA2000: MemoryStream not disposed
        public byte[] GetBytes(string text)
        {
            var stream = new MemoryStream();  // CA2000
            var writer = new StreamWriter(stream);  // CA2000
            writer.Write(text);
            writer.Flush();
            return stream.ToArray();
        }

        // CA2000: HttpClient created but not disposed properly
        public string FetchData(string url)
        {
            var client = new HttpClient();  // CA2000
            var response = client.GetStringAsync(url).Result;
            return response;
            // client is not disposed
        }

        // CA2000: In conditional - not disposed in all paths
        public void ConditionalResource(bool condition)
        {
            var reader = new StreamReader("file.txt");  // CA2000
            if (condition)
            {
                Console.WriteLine(reader.ReadToEnd());
            }
            // reader not disposed when condition is false
        }
    }

    /// <summary>
    /// Resource leaks in exception scenarios
    /// </summary>
    public class ExceptionResourceLeaks
    {
        // CA2000: Not disposed if exception occurs
        public void UnsafeResourceUsage(string path)
        {
            var stream = new FileStream(path, FileMode.Open);  // CA2000
            var data = new byte[100];
            stream.Read(data, 0, 100);  // May throw
            stream.Dispose();  // Never reached if exception
        }

        // CA2000: Try without finally dispose
        public void PartiallyHandled(string path)
        {
            StreamReader? reader = null;
            try
            {
                reader = new StreamReader(path);  // CA2000
                Console.WriteLine(reader.ReadToEnd());
            }
            catch (IOException)
            {
                // reader not disposed in catch
            }
        }
    }

    /// <summary>
    /// Clean resource management patterns
    /// </summary>
    public class SafeResourceExamples
    {
        // OK: Using statement
        public string ReadFileContent(string path)
        {
            using var reader = new StreamReader(path);
            return reader.ReadToEnd();
        }

        // OK: Using block
        public void WriteToFile(string path, string content)
        {
            using (var stream = new FileStream(path, FileMode.Create))
            using (var writer = new StreamWriter(stream))
            {
                writer.Write(content);
            }
        }

        // OK: Try-finally pattern
        public void ExplicitDispose(string path)
        {
            StreamReader? reader = null;
            try
            {
                reader = new StreamReader(path);
                Console.WriteLine(reader.ReadToEnd());
            }
            finally
            {
                reader?.Dispose();
            }
        }
    }
}
