//! Complex Rust module demonstrating advanced patterns.
//! Includes traits, lifetimes, async, and error handling.

use std::collections::HashMap;
use std::fmt;
use std::sync::{Arc, Mutex};

/// A trait for entities that can be stored in a repository.
pub trait Entity {
    fn id(&self) -> u64;
}

/// A trait for repositories with generic CRUD operations.
pub trait Repository<T: Entity> {
    type Error: fmt::Debug;

    fn find(&self, id: u64) -> Result<Option<T>, Self::Error>;
    fn find_all(&self) -> Result<Vec<T>, Self::Error>;
    fn save(&mut self, entity: T) -> Result<T, Self::Error>;
    fn delete(&mut self, id: u64) -> Result<bool, Self::Error>;
}

/// An in-memory repository implementation.
pub struct InMemoryRepository<T: Entity + Clone> {
    items: HashMap<u64, T>,
}

impl<T: Entity + Clone> InMemoryRepository<T> {
    pub fn new() -> Self {
        InMemoryRepository {
            items: HashMap::new(),
        }
    }
}

impl<T: Entity + Clone> Default for InMemoryRepository<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T: Entity + Clone> Repository<T> for InMemoryRepository<T> {
    type Error = &'static str;

    fn find(&self, id: u64) -> Result<Option<T>, Self::Error> {
        Ok(self.items.get(&id).cloned())
    }

    fn find_all(&self) -> Result<Vec<T>, Self::Error> {
        Ok(self.items.values().cloned().collect())
    }

    fn save(&mut self, entity: T) -> Result<T, Self::Error> {
        let id = entity.id();
        self.items.insert(id, entity.clone());
        Ok(entity)
    }

    fn delete(&mut self, id: u64) -> Result<bool, Self::Error> {
        Ok(self.items.remove(&id).is_some())
    }
}

/// A thread-safe repository wrapper.
pub struct ThreadSafeRepository<T: Entity + Clone + Send> {
    inner: Arc<Mutex<InMemoryRepository<T>>>,
}

impl<T: Entity + Clone + Send> ThreadSafeRepository<T> {
    pub fn new() -> Self {
        ThreadSafeRepository {
            inner: Arc::new(Mutex::new(InMemoryRepository::new())),
        }
    }

    pub fn find(&self, id: u64) -> Result<Option<T>, &'static str> {
        let repo = self.inner.lock().map_err(|_| "lock poisoned")?;
        repo.find(id)
    }

    pub fn save(&self, entity: T) -> Result<T, &'static str> {
        let mut repo = self.inner.lock().map_err(|_| "lock poisoned")?;
        repo.save(entity)
    }
}

impl<T: Entity + Clone + Send> Default for ThreadSafeRepository<T> {
    fn default() -> Self {
        Self::new()
    }
}

/// A builder pattern implementation.
#[derive(Default)]
pub struct RequestBuilder {
    method: Option<String>,
    url: Option<String>,
    headers: HashMap<String, String>,
    body: Option<String>,
}

impl RequestBuilder {
    pub fn new() -> Self {
        RequestBuilder::default()
    }

    pub fn method(mut self, method: &str) -> Self {
        self.method = Some(method.to_string());
        self
    }

    pub fn url(mut self, url: &str) -> Self {
        self.url = Some(url.to_string());
        self
    }

    pub fn header(mut self, key: &str, value: &str) -> Self {
        self.headers.insert(key.to_string(), value.to_string());
        self
    }

    pub fn body(mut self, body: &str) -> Self {
        self.body = Some(body.to_string());
        self
    }

    pub fn build(self) -> Result<Request, &'static str> {
        let method = self.method.ok_or("method is required")?;
        let url = self.url.ok_or("url is required")?;

        Ok(Request {
            method,
            url,
            headers: self.headers,
            body: self.body,
        })
    }
}

/// A request struct built by RequestBuilder.
#[derive(Debug)]
pub struct Request {
    pub method: String,
    pub url: String,
    pub headers: HashMap<String, String>,
    pub body: Option<String>,
}

/// A result type with detailed error information.
pub enum AppError {
    NotFound { resource: String, id: u64 },
    Validation { field: String, message: String },
    Internal { message: String },
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::NotFound { resource, id } => {
                write!(f, "{} with id {} not found", resource, id)
            }
            AppError::Validation { field, message } => {
                write!(f, "Validation error on {}: {}", field, message)
            }
            AppError::Internal { message } => {
                write!(f, "Internal error: {}", message)
            }
        }
    }
}

impl fmt::Debug for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(self, f)
    }
}

impl std::error::Error for AppError {}

/// A struct demonstrating lifetime annotations.
pub struct Parser<'a> {
    input: &'a str,
    position: usize,
}

impl<'a> Parser<'a> {
    pub fn new(input: &'a str) -> Self {
        Parser { input, position: 0 }
    }

    pub fn peek(&self) -> Option<char> {
        self.input[self.position..].chars().next()
    }

    pub fn advance(&mut self) -> Option<char> {
        let c = self.peek()?;
        self.position += c.len_utf8();
        Some(c)
    }

    pub fn parse_identifier(&mut self) -> Option<&'a str> {
        let start = self.position;

        while let Some(c) = self.peek() {
            if c.is_alphanumeric() || c == '_' {
                self.advance();
            } else {
                break;
            }
        }

        if self.position > start {
            Some(&self.input[start..self.position])
        } else {
            None
        }
    }

    pub fn skip_whitespace(&mut self) {
        while let Some(c) = self.peek() {
            if c.is_whitespace() {
                self.advance();
            } else {
                break;
            }
        }
    }
}

/// A state machine implementation.
#[derive(Debug, Clone, PartialEq)]
pub enum State {
    Idle,
    Running,
    Paused,
    Stopped,
}

pub struct StateMachine {
    state: State,
    transitions: HashMap<(State, String), State>,
}

impl StateMachine {
    pub fn new() -> Self {
        let mut transitions = HashMap::new();

        transitions.insert((State::Idle, "start".to_string()), State::Running);
        transitions.insert((State::Running, "pause".to_string()), State::Paused);
        transitions.insert((State::Running, "stop".to_string()), State::Stopped);
        transitions.insert((State::Paused, "resume".to_string()), State::Running);
        transitions.insert((State::Paused, "stop".to_string()), State::Stopped);

        StateMachine {
            state: State::Idle,
            transitions,
        }
    }

    pub fn current_state(&self) -> &State {
        &self.state
    }

    pub fn transition(&mut self, action: &str) -> Result<&State, &'static str> {
        let key = (self.state.clone(), action.to_string());

        if let Some(next_state) = self.transitions.get(&key) {
            self.state = next_state.clone();
            Ok(&self.state)
        } else {
            Err("invalid transition")
        }
    }
}

impl Default for StateMachine {
    fn default() -> Self {
        Self::new()
    }
}

/// An iterator adapter for chunking.
pub struct Chunks<I: Iterator> {
    iter: I,
    size: usize,
}

impl<I: Iterator> Chunks<I> {
    pub fn new(iter: I, size: usize) -> Self {
        assert!(size > 0, "chunk size must be positive");
        Chunks { iter, size }
    }
}

impl<I: Iterator> Iterator for Chunks<I> {
    type Item = Vec<I::Item>;

    fn next(&mut self) -> Option<Self::Item> {
        let mut chunk = Vec::with_capacity(self.size);

        for _ in 0..self.size {
            if let Some(item) = self.iter.next() {
                chunk.push(item);
            } else {
                break;
            }
        }

        if chunk.is_empty() {
            None
        } else {
            Some(chunk)
        }
    }
}

/// Extension trait for iterators to add chunking.
pub trait ChunkExt: Iterator + Sized {
    fn chunks(self, size: usize) -> Chunks<Self> {
        Chunks::new(self, size)
    }
}

impl<I: Iterator> ChunkExt for I {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_state_machine() {
        let mut sm = StateMachine::new();
        assert_eq!(*sm.current_state(), State::Idle);

        sm.transition("start").unwrap();
        assert_eq!(*sm.current_state(), State::Running);

        sm.transition("pause").unwrap();
        assert_eq!(*sm.current_state(), State::Paused);
    }

    #[test]
    fn test_chunks() {
        let data = vec![1, 2, 3, 4, 5];
        let chunks: Vec<_> = data.into_iter().chunks(2).collect();
        assert_eq!(chunks, vec![vec![1, 2], vec![3, 4], vec![5]]);
    }

    #[test]
    fn test_request_builder() {
        let request = RequestBuilder::new()
            .method("POST")
            .url("https://api.example.com")
            .header("Content-Type", "application/json")
            .body(r#"{"key": "value"}"#)
            .build()
            .unwrap();

        assert_eq!(request.method, "POST");
        assert_eq!(request.url, "https://api.example.com");
    }
}
