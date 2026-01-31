/**
 * Test file for Hardcoded Secrets/Credentials detection.
 * Contains multiple hardcoded credential patterns for TypeScript.
 */

// HARDCODED_SECRET: Hardcoded password in constant
const ADMIN_PASSWORD = "SuperSecretPassword123!";

// HARDCODED_SECRET: Hardcoded API key
const API_KEY = "sk-1234567890abcdef1234567890abcdef";

// HARDCODED_SECRET: Hardcoded connection string with password
const DATABASE_URL = "postgresql://admin:Pr0dP@ssw0rd!@prod.db.com:5432/users";

interface DatabaseConfig {
    host: string;
    password: string;
}

// HARDCODED_SECRET: Hardcoded secret in object
const dbConfig: DatabaseConfig = {
    host: "localhost",
    password: "LocalDevPassword123",
};

// HARDCODED_SECRET: Hardcoded token
const AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U";

// GOOD: Using environment variable
function getApiKey(): string {
    const key = process.env.API_KEY;
    if (!key) {
        throw new Error("API_KEY environment variable not set");
    }
    return key;
}

// GOOD: Using config from environment
function getDatabaseUrl(): string {
    return process.env.DATABASE_URL || "postgres://localhost/dev";
}

// GOOD: Placeholder that must be replaced
const TEMPLATE_KEY = "<YOUR_API_KEY_HERE>";

class AuthService {
    private secretKey: string;

    constructor() {
        // GOOD: Getting secret from environment
        const secret = process.env.JWT_SECRET;
        if (!secret) {
            throw new Error("JWT_SECRET must be set");
        }
        this.secretKey = secret;
    }

    generateToken(userId: string): string {
        // Implementation would use this.secretKey
        return `token-for-${userId}`;
    }
}

export {
    ADMIN_PASSWORD,
    API_KEY,
    DATABASE_URL,
    dbConfig,
    AUTH_TOKEN,
    TEMPLATE_KEY,
    getApiKey,
    getDatabaseUrl,
    AuthService,
};
