// Path Traversal test cases for DevSkim evaluation
// Expected: DevSkim should detect path traversal vulnerabilities

using System;
using System.IO;

namespace SecurityTests
{
    public class PathTraversal
    {
        private const string BaseDirectory = "/var/www/uploads";

        // VULNERABLE: Direct user input in file path (DS175862)
        public string ReadFile(string filename)
        {
            string path = "/uploads/" + filename;
            return File.ReadAllText(path);
            // DevSkim should flag this as path traversal
        }

        // VULNERABLE: User input in Path.Combine (DS162155)
        public void SaveFile(string userFilename, byte[] content)
        {
            string path = Path.Combine(BaseDirectory, userFilename);
            File.WriteAllBytes(path, content);
            // DevSkim should flag this
        }

        // VULNERABLE: Directory traversal (DS172411)
        public string[] ListDirectory(string subdirectory)
        {
            string path = BaseDirectory + "/" + subdirectory;
            return Directory.GetFiles(path);
            // DevSkim should flag this
        }

        // VULNERABLE: File stream with user input
        public void OpenFileStream(string filename)
        {
            using (var stream = new FileStream(filename, FileMode.Open))
            {
                // Process file
            }
            // DevSkim should flag this
        }

        // SAFE: Validated and sanitized path
        public string ReadFileSafe(string filename)
        {
            // Remove any path traversal characters
            string sanitized = Path.GetFileName(filename);
            string fullPath = Path.Combine(BaseDirectory, sanitized);

            // Ensure path is within base directory
            if (!fullPath.StartsWith(BaseDirectory))
            {
                throw new UnauthorizedAccessException();
            }

            return File.ReadAllText(fullPath);
            // This should NOT be flagged (defense in depth)
        }

        // SAFE: Whitelisted paths only
        public string ReadWhitelistedFile(int fileId)
        {
            var allowedFiles = new Dictionary<int, string>
            {
                { 1, "readme.txt" },
                { 2, "config.json" }
            };

            if (allowedFiles.TryGetValue(fileId, out string filename))
            {
                return File.ReadAllText(Path.Combine(BaseDirectory, filename));
            }

            throw new FileNotFoundException();
            // This should NOT be flagged
        }
    }
}
