/// Test file for Hardcoded Secrets/Credentials detection.
/// Contains multiple hardcoded credential patterns for Rust.

use std::env;

// HARDCODED_SECRET: Hardcoded password in constant
const ADMIN_PASSWORD: &str = "SuperSecretPassword123!";

// HARDCODED_SECRET: Hardcoded API key
const API_KEY: &str = "sk-1234567890abcdef1234567890abcdef";

// HARDCODED_SECRET: Hardcoded connection string with password
const DATABASE_URL: &str = "postgresql://admin:Pr0dP@ssw0rd!@prod.db.com:5432/users";

pub struct Config {
    pub db_host: String,
    pub db_password: String,
}

// HARDCODED_SECRET: Hardcoded secret in struct initialization
pub fn get_hardcoded_config() -> Config {
    Config {
        db_host: "localhost".to_string(),
        db_password: "LocalDevPassword123".to_string(),
    }
}

// GOOD: Using environment variable
pub fn get_api_key() -> Result<String, env::VarError> {
    env::var("API_KEY")
}

// GOOD: Using environment variable for database URL
pub fn get_database_url() -> String {
    env::var("DATABASE_URL").unwrap_or_else(|_| "postgres://localhost/dev".to_string())
}

// GOOD: Getting config from environment
pub fn get_config_from_env() -> Result<Config, env::VarError> {
    Ok(Config {
        db_host: env::var("DB_HOST")?,
        db_password: env::var("DB_PASSWORD")?,
    })
}

pub struct AuthService {
    secret_key: String,
}

impl AuthService {
    // GOOD: Constructor that requires secret from caller
    pub fn new(secret_key: String) -> Self {
        Self { secret_key }
    }

    // GOOD: Factory method using environment variable
    pub fn from_env() -> Result<Self, env::VarError> {
        let secret_key = env::var("JWT_SECRET")?;
        Ok(Self { secret_key })
    }

    pub fn generate_token(&self, user_id: &str) -> String {
        format!("token-for-{}-{}", user_id, &self.secret_key[..8])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_api_key_from_env() {
        // Test uses environment variable, not hardcoded value
        env::set_var("API_KEY", "test-key");
        assert!(get_api_key().is_ok());
    }
}
