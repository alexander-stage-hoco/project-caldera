// Insecure Random Number Generation test cases for DevSkim evaluation
// Expected: DevSkim should detect weak random number generators

using System;
using System.Security.Cryptography;

namespace SecurityTests
{
    public class InsecureRandom
    {
        // VULNERABLE: System.Random for security purposes (DS148264)
        public string GenerateToken()
        {
            var random = new Random();  // Not cryptographically secure
            var bytes = new byte[32];
            random.NextBytes(bytes);
            return Convert.ToBase64String(bytes);
            // DevSkim should flag System.Random for security-sensitive operations
        }

        // VULNERABLE: System.Random for session ID
        public string GenerateSessionId()
        {
            var random = new Random();
            return random.Next().ToString("X8") + random.Next().ToString("X8");
            // DevSkim should flag this
        }

        // VULNERABLE: Seeded with predictable value
        public int GetPredictableRandom()
        {
            var random = new Random(12345);  // Predictable seed
            return random.Next();
        }

        // VULNERABLE: Time-based seed (predictable)
        public int GetTimeSeedRandom()
        {
            var random = new Random(DateTime.Now.Millisecond);  // Weak seed
            return random.Next();
        }

        // VULNERABLE: GUID used for security token
        public string GenerateGuidToken()
        {
            // GUIDs are not cryptographically random
            return Guid.NewGuid().ToString();
        }

        // SAFE: RNGCryptoServiceProvider (legacy but secure)
        public byte[] GenerateSecureBytes()
        {
            using (var rng = new RNGCryptoServiceProvider())
            {
                var bytes = new byte[32];
                rng.GetBytes(bytes);
                return bytes;
            }
            // This should NOT be flagged
        }

        // SAFE: RandomNumberGenerator (modern secure API)
        public string GenerateSecureToken()
        {
            var bytes = new byte[32];
            RandomNumberGenerator.Fill(bytes);
            return Convert.ToBase64String(bytes);
            // This should NOT be flagged
        }

        // SAFE: System.Random for non-security purposes (games, simulations)
        public int RollDice()
        {
            // Using Random for non-security purpose is acceptable
            var random = new Random();
            return random.Next(1, 7);
            // This might still be flagged, but is a known limitation
        }
    }
}
