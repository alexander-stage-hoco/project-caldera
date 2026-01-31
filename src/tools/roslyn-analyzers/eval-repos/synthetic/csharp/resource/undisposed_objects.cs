using System;
using System.IO;
using System.Net;
using System.Data.SqlClient;

namespace SyntheticSmells.Resource
{
    /// <summary>
    /// Undisposed object examples for Roslyn Analyzer testing.
    /// Expected violations: CA2000 (6) = 6 total
    /// </summary>
    public class UndisposedObjectsExamples
    {
        // CA2000: FileStream not disposed (line 16)
        public void ReadFileWrong(string path)
        {
            var stream = new FileStream(path, FileMode.Open);
            var data = new byte[stream.Length];
            stream.Read(data, 0, data.Length);
            // stream is never disposed!
        }

        // CA2000: StreamReader not disposed (line 26)
        public string ReadTextWrong(string path)
        {
            var reader = new StreamReader(path);
            return reader.ReadToEnd();
            // reader is never disposed!
        }

        // CA2000: SqlConnection not disposed (line 35)
        public void QueryDatabaseWrong(string query)
        {
            var conn = new SqlConnection("...");
            conn.Open();
            var cmd = new SqlCommand(query, conn);
            cmd.ExecuteNonQuery();
            // conn and cmd are never disposed!
        }

        // CA2000: HttpWebRequest response not disposed (line 45)
        public string FetchUrlWrong(string url)
        {
            var request = WebRequest.Create(url);
            var response = request.GetResponse();
            using var reader = new StreamReader(response.GetResponseStream());
            return reader.ReadToEnd();
            // response is never disposed!
        }

        // CA2000: MemoryStream not disposed (line 56)
        public byte[] CreateBufferWrong()
        {
            var stream = new MemoryStream();
            stream.Write(new byte[] { 1, 2, 3 }, 0, 3);
            return stream.ToArray();
            // stream is never disposed!
        }

        // CA2000: Multiple disposables not disposed (line 66)
        public void ProcessDataWrong(string input, string output)
        {
            var inputStream = new FileStream(input, FileMode.Open);
            var outputStream = new FileStream(output, FileMode.Create);
            var buffer = new byte[1024];
            int read;
            while ((read = inputStream.Read(buffer, 0, buffer.Length)) > 0)
            {
                outputStream.Write(buffer, 0, read);
            }
            // Neither stream is disposed!
        }

        // OK: Using statement (no violation)
        public void ReadFileCorrect(string path)
        {
            using var stream = new FileStream(path, FileMode.Open);
            var data = new byte[stream.Length];
            stream.Read(data, 0, data.Length);
        }

        // OK: Using block (no violation)
        public string ReadTextCorrect(string path)
        {
            using (var reader = new StreamReader(path))
            {
                return reader.ReadToEnd();
            }
        }
    }
}
