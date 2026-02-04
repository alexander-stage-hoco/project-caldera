//! Rust file with heavy duplication - multiple large duplicated blocks.

/// Report item representation.
pub struct ReportItem {
    pub id: Option<String>,
    pub name: Option<String>,
    pub email: Option<String>,
    pub status: Option<String>,
    pub created_at: Option<String>,
}

/// Generate a formatted report for users.
pub fn generate_user_report(users: &[ReportItem]) -> String {
    let mut lines = Vec::new();
    lines.push("=".repeat(60));
    lines.push("USER REPORT".to_string());
    lines.push("=".repeat(60));
    lines.push(String::new());

    for item in users {
        let id = item.id.as_deref().unwrap_or("N/A");
        let name = item.name.as_deref().unwrap_or("Unknown");
        let email = item.email.as_deref().unwrap_or("N/A");
        let status = item.status.as_deref().unwrap_or("active");
        let created_at = item.created_at.as_deref().unwrap_or("Unknown");
        lines.push(format!("ID: {}", id));
        lines.push(format!("Name: {}", name));
        lines.push(format!("Email: {}", email));
        lines.push(format!("Status: {}", status));
        lines.push(format!("Created: {}", created_at));
        lines.push("-".repeat(40));
    }

    lines.push(String::new());
    lines.push(format!("Total records: {}", users.len()));
    lines.push("=".repeat(60));
    lines.join("\n")
}

/// Generate a formatted report for admins - duplicated structure.
pub fn generate_admin_report(admins: &[ReportItem]) -> String {
    let mut lines = Vec::new();
    lines.push("=".repeat(60));
    lines.push("ADMIN REPORT".to_string());
    lines.push("=".repeat(60));
    lines.push(String::new());

    for item in admins {
        let id = item.id.as_deref().unwrap_or("N/A");
        let name = item.name.as_deref().unwrap_or("Unknown");
        let email = item.email.as_deref().unwrap_or("N/A");
        let status = item.status.as_deref().unwrap_or("active");
        let created_at = item.created_at.as_deref().unwrap_or("Unknown");
        lines.push(format!("ID: {}", id));
        lines.push(format!("Name: {}", name));
        lines.push(format!("Email: {}", email));
        lines.push(format!("Status: {}", status));
        lines.push(format!("Created: {}", created_at));
        lines.push("-".repeat(40));
    }

    lines.push(String::new());
    lines.push(format!("Total records: {}", admins.len()));
    lines.push("=".repeat(60));
    lines.join("\n")
}

/// Generate a formatted report for guests - duplicated structure.
pub fn generate_guest_report(guests: &[ReportItem]) -> String {
    let mut lines = Vec::new();
    lines.push("=".repeat(60));
    lines.push("GUEST REPORT".to_string());
    lines.push("=".repeat(60));
    lines.push(String::new());

    for item in guests {
        let id = item.id.as_deref().unwrap_or("N/A");
        let name = item.name.as_deref().unwrap_or("Unknown");
        let email = item.email.as_deref().unwrap_or("N/A");
        let status = item.status.as_deref().unwrap_or("active");
        let created_at = item.created_at.as_deref().unwrap_or("Unknown");
        lines.push(format!("ID: {}", id));
        lines.push(format!("Name: {}", name));
        lines.push(format!("Email: {}", email));
        lines.push(format!("Status: {}", status));
        lines.push(format!("Created: {}", created_at));
        lines.push("-".repeat(40));
    }

    lines.push(String::new());
    lines.push(format!("Total records: {}", guests.len()));
    lines.push("=".repeat(60));
    lines.join("\n")
}

/// Input data for validation.
pub struct InputData {
    pub name: Option<String>,
    pub email: Option<String>,
    pub password: Option<String>,
    pub age: Option<u32>,
}

/// Validate user input data.
pub fn validate_user_input(data: &InputData) -> Vec<String> {
    let mut errors = Vec::new();
    if data.name.is_none() || data.name.as_ref().map(|s| s.is_empty()).unwrap_or(true) {
        errors.push("Name is required".to_string());
    }
    if data.email.is_none() || data.email.as_ref().map(|s| s.is_empty()).unwrap_or(true) {
        errors.push("Email is required".to_string());
    }
    if !data.email.as_ref().map(|s| s.contains('@')).unwrap_or(false) {
        errors.push("Invalid email format".to_string());
    }
    if data.password.is_none() || data.password.as_ref().map(|s| s.is_empty()).unwrap_or(true) {
        errors.push("Password is required".to_string());
    }
    if data.password.as_ref().map(|s| s.len()).unwrap_or(0) < 8 {
        errors.push("Password must be at least 8 characters".to_string());
    }
    if data.age.is_none() {
        errors.push("Age is required".to_string());
    }
    if data.age.unwrap_or(0) < 18 {
        errors.push("Must be at least 18 years old".to_string());
    }
    errors
}

/// Validate admin input data - duplicated validation.
pub fn validate_admin_input(data: &InputData) -> Vec<String> {
    let mut errors = Vec::new();
    if data.name.is_none() || data.name.as_ref().map(|s| s.is_empty()).unwrap_or(true) {
        errors.push("Name is required".to_string());
    }
    if data.email.is_none() || data.email.as_ref().map(|s| s.is_empty()).unwrap_or(true) {
        errors.push("Email is required".to_string());
    }
    if !data.email.as_ref().map(|s| s.contains('@')).unwrap_or(false) {
        errors.push("Invalid email format".to_string());
    }
    if data.password.is_none() || data.password.as_ref().map(|s| s.is_empty()).unwrap_or(true) {
        errors.push("Password is required".to_string());
    }
    if data.password.as_ref().map(|s| s.len()).unwrap_or(0) < 8 {
        errors.push("Password must be at least 8 characters".to_string());
    }
    if data.age.is_none() {
        errors.push("Age is required".to_string());
    }
    if data.age.unwrap_or(0) < 18 {
        errors.push("Must be at least 18 years old".to_string());
    }
    errors
}
