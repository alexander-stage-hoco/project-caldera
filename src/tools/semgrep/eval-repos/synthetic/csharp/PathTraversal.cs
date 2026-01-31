/**
 * Test file for Path Traversal vulnerability detection.
 * Contains directory traversal patterns for C#.
 */

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;

namespace SmellTests.Security
{
    public class PathTraversalController : Controller
    {
        private readonly string _basePath = "/var/www/uploads";

        // PATH_TRAVERSAL: Direct file path from user input
        public IActionResult DownloadFile(string fileName)
        {
            // BAD: User input directly used in file path
            string filePath = Path.Combine(_basePath, fileName);
            byte[] fileBytes = System.IO.File.ReadAllBytes(filePath);
            return File(fileBytes, "application/octet-stream", fileName);
        }

        // PATH_TRAVERSAL: Reading file with user-controlled path
        public string ReadConfig(string configName)
        {
            // BAD: Path concatenation with user input
            string path = "/etc/app/configs/" + configName;
            return System.IO.File.ReadAllText(path);
        }

        // PATH_TRAVERSAL: File.OpenRead with user input
        public Stream GetDocument(string docPath)
        {
            // BAD: Opening file with user-controlled path
            return System.IO.File.OpenRead(docPath);
        }

        // PATH_TRAVERSAL: Directory listing with user input
        public string[] ListFiles(string directory)
        {
            // BAD: User controls directory path
            string path = Path.Combine(_basePath, directory);
            return Directory.GetFiles(path);
        }

        // PATH_TRAVERSAL: File creation with user input
        public async Task SaveUpload(string fileName, IFormFile file)
        {
            // BAD: User controls file name (could include ../)
            string filePath = Path.Combine(_basePath, fileName);
            using var stream = new FileStream(filePath, FileMode.Create);
            await file.CopyToAsync(stream);
        }

        // PATH_TRAVERSAL: File deletion with user input
        public IActionResult DeleteFile(string fileName)
        {
            // BAD: User controls which file to delete
            string filePath = Path.Combine(_basePath, fileName);
            System.IO.File.Delete(filePath);
            return Ok("File deleted");
        }

        // PATH_TRAVERSAL: StreamReader with user path
        public string ReadTextFile(string userPath)
        {
            // BAD: User-controlled path in StreamReader
            using var reader = new StreamReader(userPath);
            return reader.ReadToEnd();
        }

        // PATH_TRAVERSAL: FileInfo with user input
        public long GetFileSize(string fileName)
        {
            // BAD: User input in FileInfo
            var fileInfo = new FileInfo(Path.Combine(_basePath, fileName));
            return fileInfo.Length;
        }

        // PATH_TRAVERSAL: Using string interpolation
        public byte[] GetImage(string imageName)
        {
            // BAD: String interpolation with user input
            string imagePath = $"/var/www/images/{imageName}";
            return System.IO.File.ReadAllBytes(imagePath);
        }

        // PATH_TRAVERSAL: Multiple path segments
        public string ReadUserFile(string userId, string fileName)
        {
            // BAD: Multiple user inputs in path (any could be traversal)
            string path = Path.Combine(_basePath, userId, "documents", fileName);
            return System.IO.File.ReadAllText(path);
        }

        // CORRECT: Validating file name
        public IActionResult DownloadFileSafe(string fileName)
        {
            // GOOD: Validate file name has no path separators
            if (fileName.Contains("..") || fileName.Contains("/") || fileName.Contains("\\"))
            {
                return BadRequest("Invalid file name");
            }

            string filePath = Path.Combine(_basePath, fileName);

            // GOOD: Verify resolved path is within base directory
            string fullPath = Path.GetFullPath(filePath);
            if (!fullPath.StartsWith(_basePath))
            {
                return BadRequest("Invalid path");
            }

            byte[] fileBytes = System.IO.File.ReadAllBytes(fullPath);
            return File(fileBytes, "application/octet-stream", fileName);
        }

        // CORRECT: Using Path.GetFileName to sanitize
        public IActionResult SaveFileSafe(string fileName, IFormFile file)
        {
            // GOOD: Extract just the filename, removing any path
            string safeFileName = Path.GetFileName(fileName);
            string filePath = Path.Combine(_basePath, safeFileName);

            using var stream = new FileStream(filePath, FileMode.Create);
            file.CopyTo(stream);

            return Ok();
        }

        // CORRECT: Whitelist approach
        public string ReadConfigSafe(string configName)
        {
            // GOOD: Whitelist of allowed configs
            var allowedConfigs = new[] { "app.json", "database.json", "logging.json" };
            if (!allowedConfigs.Contains(configName))
            {
                throw new ArgumentException("Invalid config name");
            }

            string path = Path.Combine("/etc/app/configs", configName);
            return System.IO.File.ReadAllText(path);
        }
    }
}
