//! Simple Rust module demonstrating basic patterns and ownership.

/// A simple user struct with basic fields.
#[derive(Debug, Clone)]
pub struct User {
    pub id: u32,
    pub name: String,
    pub email: String,
    pub active: bool,
}

impl User {
    /// Creates a new user with the given details.
    pub fn new(id: u32, name: String, email: String) -> Self {
        User {
            id,
            name,
            email,
            active: true,
        }
    }

    /// Returns a greeting message for the user.
    pub fn greet(&self) -> String {
        format!("Hello, {}!", self.name)
    }

    /// Checks if the user has a valid email.
    pub fn is_valid(&self) -> bool {
        self.id > 0 && !self.name.is_empty() && self.email.contains('@')
    }

    /// Deactivates the user.
    pub fn deactivate(&mut self) {
        self.active = false;
    }
}

/// A simple counter implementation.
pub struct Counter {
    value: i32,
}

impl Counter {
    /// Creates a new counter with the given initial value.
    pub fn new(initial: i32) -> Self {
        Counter { value: initial }
    }

    /// Increments the counter by 1.
    pub fn increment(&mut self) {
        self.value += 1;
    }

    /// Decrements the counter by 1.
    pub fn decrement(&mut self) {
        self.value -= 1;
    }

    /// Returns the current value.
    pub fn value(&self) -> i32 {
        self.value
    }
}

/// Adds two numbers.
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

/// Multiplies two numbers.
pub fn multiply(a: i32, b: i32) -> i32 {
    a * b
}

/// Divides a by b, returning an error if b is zero.
pub fn divide(a: i32, b: i32) -> Result<i32, &'static str> {
    if b == 0 {
        Err("division by zero")
    } else {
        Ok(a / b)
    }
}

/// Filters a vector of users to only include active ones.
pub fn filter_active_users(users: Vec<User>) -> Vec<User> {
    users.into_iter().filter(|u| u.active).collect()
}

/// Maps a vector of users to their names.
pub fn map_user_names(users: &[User]) -> Vec<String> {
    users.iter().map(|u| u.name.clone()).collect()
}

/// An enum representing different statuses.
#[derive(Debug, Clone, PartialEq)]
pub enum Status {
    Pending,
    Active,
    Completed,
    Failed(String),
}

impl Status {
    /// Checks if the status is a success state.
    pub fn is_success(&self) -> bool {
        matches!(self, Status::Completed)
    }

    /// Checks if the status is a failure state.
    pub fn is_failure(&self) -> bool {
        matches!(self, Status::Failed(_))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_user_creation() {
        let user = User::new(1, "Alice".to_string(), "alice@example.com".to_string());
        assert_eq!(user.id, 1);
        assert_eq!(user.name, "Alice");
        assert!(user.active);
    }

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
    }

    #[test]
    fn test_divide() {
        assert_eq!(divide(10, 2), Ok(5));
        assert_eq!(divide(10, 0), Err("division by zero"));
    }
}
