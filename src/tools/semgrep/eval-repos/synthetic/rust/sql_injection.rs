/// Test file for SQL injection vulnerability detection.
/// Contains multiple SQL injection patterns for Rust.

use sqlx::{Pool, Postgres, Row};

pub struct User {
    pub id: i32,
    pub username: String,
    pub email: String,
}

// SQL INJECTION: String interpolation in SQL query
pub async fn get_user_by_name(pool: &Pool<Postgres>, username: &str) -> Result<User, sqlx::Error> {
    let query = format!("SELECT * FROM users WHERE username = '{}'", username);
    let row = sqlx::query(&query).fetch_one(pool).await?;
    Ok(User { id: row.get("id"), username: row.get("username"), email: row.get("email") })
}

// SQL INJECTION: String concatenation in SQL query
pub async fn search_products(pool: &Pool<Postgres>, search_term: &str) -> Result<Vec<String>, sqlx::Error> {
    let query = "SELECT name FROM products WHERE name LIKE '%".to_owned() + search_term + "%'";
    let rows = sqlx::query(&query).fetch_all(pool).await?;
    Ok(rows.iter().map(|r| r.get("name")).collect())
}

// SQL INJECTION: Direct format! interpolation
pub async fn delete_user(pool: &Pool<Postgres>, user_id: &str) -> Result<(), sqlx::Error> {
    let query = format!("DELETE FROM users WHERE id = {}", user_id);
    sqlx::query(&query).execute(pool).await?;
    Ok(())
}

// SQL INJECTION: Multiple injectable parameters
pub async fn update_email(pool: &Pool<Postgres>, user_id: &str, email: &str) -> Result<(), sqlx::Error> {
    let query = format!("UPDATE users SET email = '{}' WHERE id = {}", email, user_id);
    sqlx::query(&query).execute(pool).await?;
    Ok(())
}

// SQL INJECTION: String interpolation with date range
pub async fn get_orders_by_date(pool: &Pool<Postgres>, start: &str, end: &str) -> Result<Vec<i32>, sqlx::Error> {
    let query = format!("SELECT id FROM orders WHERE created_at BETWEEN '{}' AND '{}'", start, end);
    let rows = sqlx::query(&query).fetch_all(pool).await?;
    Ok(rows.iter().map(|r| r.get("id")).collect())
}

// SAFE: Parameterized query
pub async fn safe_get_user(pool: &Pool<Postgres>, user_id: i32) -> Result<User, sqlx::Error> {
    let row = sqlx::query("SELECT * FROM users WHERE id = $1")
        .bind(user_id)
        .fetch_one(pool)
        .await?;
    Ok(User { id: row.get("id"), username: row.get("username"), email: row.get("email") })
}

// SAFE: Using query macro with compile-time checking
pub async fn safe_search(pool: &Pool<Postgres>, term: &str) -> Result<Vec<String>, sqlx::Error> {
    let rows = sqlx::query!("SELECT name FROM products WHERE name ILIKE $1", format!("%{}%", term))
        .fetch_all(pool)
        .await?;
    Ok(rows.iter().map(|r| r.name.clone().unwrap_or_default()).collect())
}
