/// Test file for DD smell D1_EMPTY_CATCH equivalent in Rust.
/// Contains multiple ignored Result patterns.

use std::fs;
use std::io::Read;

/// D1_EMPTY_CATCH equivalent: Using unwrap_or_default to ignore errors
pub fn read_file_content_silent(path: &str) -> String {
    fs::read_to_string(path).unwrap_or_default()
}

/// D1_EMPTY_CATCH equivalent: Ignoring Result with let _ =
pub fn process_file_ignored(path: &str) {
    let _ = fs::remove_file(path);  // BAD: Error completely ignored
}

/// D1_EMPTY_CATCH equivalent: Empty match arm for Err
pub fn parse_config(content: &str) -> Option<Config> {
    match serde_json::from_str::<Config>(content) {
        Ok(config) => Some(config),
        Err(_) => None,  // BAD: Error silently swallowed
    }
}

/// D1_EMPTY_CATCH equivalent: Using ok() to discard errors
pub fn fetch_data(url: &str) -> Option<String> {
    // BAD: .ok() converts Result to Option, discarding error info
    reqwest::blocking::get(url).ok()?.text().ok()
}

/// D1_EMPTY_CATCH equivalent: Ignoring errors in loop
pub fn process_items(items: Vec<&str>) -> Vec<String> {
    items
        .iter()
        .filter_map(|item| process_item(item).ok())  // BAD: Errors silently filtered
        .collect()
}

/// D1_EMPTY_CATCH equivalent: Empty error handling
pub fn save_data(path: &str, data: &[u8]) {
    if let Err(_) = fs::write(path, data) {
        // BAD: Error acknowledged but not handled
    }
}

/// D1_EMPTY_CATCH equivalent: Using expect but ignoring why
pub fn dangerous_unwrap(path: &str) -> String {
    // BAD: unwrap_or with default hides actual error
    fs::read_to_string(path).unwrap_or(String::new())
}

// CORRECT: Proper error handling
pub fn read_file_content_correct(path: &str) -> Result<String, std::io::Error> {
    fs::read_to_string(path)
}

// CORRECT: Error is propagated
pub fn parse_config_correct(content: &str) -> Result<Config, serde_json::Error> {
    serde_json::from_str(content)
}

// CORRECT: Errors logged before discarding
pub fn process_items_correct(items: Vec<&str>) -> Vec<String> {
    items
        .iter()
        .filter_map(|item| {
            match process_item(item) {
                Ok(result) => Some(result),
                Err(e) => {
                    eprintln!("Failed to process {}: {}", item, e);
                    None
                }
            }
        })
        .collect()
}

// Helper types and functions
#[derive(Debug, serde::Deserialize)]
pub struct Config {
    pub name: String,
}

fn process_item(item: &str) -> Result<String, Box<dyn std::error::Error>> {
    Ok(item.to_uppercase())
}
