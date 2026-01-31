//! Nested module demonstrating Rust module patterns.

use std::sync::{Arc, RwLock};

/// Represents a nested item.
#[derive(Debug, Clone)]
pub struct NestedItem {
    pub id: i32,
    pub name: String,
    pub created_at: i64,
}

/// Service for managing nested items.
#[derive(Debug, Default)]
pub struct NestedService {
    items: Arc<RwLock<Vec<NestedItem>>>,
}

impl NestedService {
    /// Creates a new service.
    pub fn new() -> Self {
        NestedService {
            items: Arc::new(RwLock::new(Vec::new())),
        }
    }

    /// Adds an item.
    pub fn add(&self, item: NestedItem) {
        let mut items = self.items.write().unwrap();
        items.push(item);
    }

    /// Finds an item by ID.
    pub fn find(&self, id: i32) -> Option<NestedItem> {
        let items = self.items.read().unwrap();
        items.iter().find(|i| i.id == id).cloned()
    }

    /// Gets all items.
    pub fn get_all(&self) -> Vec<NestedItem> {
        let items = self.items.read().unwrap();
        items.clone()
    }

    /// Clears all items.
    pub fn clear(&self) -> usize {
        let mut items = self.items.write().unwrap();
        let count = items.len();
        items.clear();
        count
    }
}

/// Trait for processing items.
pub trait NestedProcessor {
    fn process(&self, item: &NestedItem) -> bool;
}

/// Async processor implementation.
pub struct AsyncProcessor;

impl NestedProcessor for AsyncProcessor {
    fn process(&self, item: &NestedItem) -> bool {
        item.id > 0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_nested_service() {
        let service = NestedService::new();
        service.add(NestedItem {
            id: 1,
            name: "Test".to_string(),
            created_at: 0,
        });
        assert!(service.find(1).is_some());
    }
}
