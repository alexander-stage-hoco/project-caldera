// Insecure Cryptography test cases for DevSkim evaluation
// Expected: DevSkim should detect weak crypto algorithms

using System;
using System.Security.Cryptography;
using System.Text;

namespace SecurityTests
{
    public class InsecureCrypto
    {
        // VULNERABLE: MD5 hash (DS161085)
        public string HashWithMD5(string input)
        {
            using (var md5 = MD5.Create())
            {
                byte[] hash = md5.ComputeHash(Encoding.UTF8.GetBytes(input));
                return BitConverter.ToString(hash).Replace("-", "");
            }
            // DevSkim should flag MD5 as insecure
        }

        // VULNERABLE: SHA1 hash (DS173287)
        public string HashWithSHA1(string input)
        {
            using (var sha1 = SHA1.Create())
            {
                byte[] hash = sha1.ComputeHash(Encoding.UTF8.GetBytes(input));
                return BitConverter.ToString(hash).Replace("-", "");
            }
            // DevSkim should flag SHA1 as insecure
        }

        // VULNERABLE: DES encryption (DS197800)
        public byte[] EncryptWithDES(byte[] data, byte[] key, byte[] iv)
        {
            using (var des = DES.Create())
            {
                des.Key = key;
                des.IV = iv;
                var encryptor = des.CreateEncryptor();
                return encryptor.TransformFinalBlock(data, 0, data.Length);
            }
            // DevSkim should flag DES as insecure
        }

        // VULNERABLE: ECB mode (DS144436)
        public byte[] EncryptWithECB(byte[] data, byte[] key)
        {
            using (var aes = Aes.Create())
            {
                aes.Mode = CipherMode.ECB;  // ECB mode is insecure
                aes.Key = key;
                var encryptor = aes.CreateEncryptor();
                return encryptor.TransformFinalBlock(data, 0, data.Length);
            }
        }

        // VULNERABLE: Weak random number generator (DS168931)
        public int GetRandomNumber()
        {
            var random = new Random();  // Not cryptographically secure
            return random.Next();
        }

        // VULNERABLE: Hardcoded IV
        public byte[] EncryptWithHardcodedIV(byte[] data, byte[] key)
        {
            byte[] iv = new byte[] { 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
                                     0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F };
            using (var aes = Aes.Create())
            {
                aes.Key = key;
                aes.IV = iv;  // Hardcoded IV is insecure
                var encryptor = aes.CreateEncryptor();
                return encryptor.TransformFinalBlock(data, 0, data.Length);
            }
        }

        // SAFE: SHA256 hash
        public string HashWithSHA256(string input)
        {
            using (var sha256 = SHA256.Create())
            {
                byte[] hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(input));
                return BitConverter.ToString(hash).Replace("-", "");
            }
            // This should NOT be flagged
        }

        // SAFE: AES with CBC and random IV
        public byte[] EncryptWithAES(byte[] data, byte[] key)
        {
            using (var aes = Aes.Create())
            {
                aes.Mode = CipherMode.CBC;
                aes.Key = key;
                aes.GenerateIV();  // Random IV
                var encryptor = aes.CreateEncryptor();
                return encryptor.TransformFinalBlock(data, 0, data.Length);
            }
            // This should NOT be flagged
        }

        // SAFE: Cryptographic random
        public int GetSecureRandomNumber()
        {
            using (var rng = RandomNumberGenerator.Create())
            {
                byte[] bytes = new byte[4];
                rng.GetBytes(bytes);
                return BitConverter.ToInt32(bytes, 0);
            }
            // This should NOT be flagged
        }
    }
}
