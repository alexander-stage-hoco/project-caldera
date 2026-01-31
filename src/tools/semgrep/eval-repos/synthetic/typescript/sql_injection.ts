/**
 * Test file for SQL injection vulnerability detection.
 * Contains multiple SQL injection patterns for TypeScript.
 */

import { Pool, QueryResult } from 'pg';

async function getUserByName(pool: Pool, username: string): Promise<QueryResult> {
    // SQL INJECTION: Template literal in SQL query
    const query = `SELECT * FROM users WHERE username = '${username}'`;
    return await pool.query(query);
}

async function searchProducts(pool: Pool, searchTerm: string): Promise<QueryResult> {
    // SQL INJECTION: String concatenation in SQL query
    const query = "SELECT * FROM products WHERE name LIKE '%" + searchTerm + "%'";
    return await pool.query(query);
}

async function deleteUser(pool: Pool, userId: string): Promise<void> {
    // SQL INJECTION: Direct string interpolation
    await pool.query("DELETE FROM users WHERE id = " + userId);
}

async function updateEmail(pool: Pool, userId: string, email: string): Promise<void> {
    // SQL INJECTION: Multiple injectable parameters
    const query = `UPDATE users SET email = '${email}' WHERE id = ${userId}`;
    await pool.query(query);
}

async function getOrdersByDate(pool: Pool, startDate: string, endDate: string): Promise<QueryResult> {
    // SQL INJECTION: String interpolation with multiple params
    const query = `SELECT * FROM orders WHERE created_at BETWEEN '${startDate}' AND '${endDate}'`;
    return await pool.query(query);
}

async function findUserByEmail(pool: Pool, email: string): Promise<QueryResult> {
    // SQL INJECTION: eval-like construction
    const query = "SELECT * FROM users WHERE email = '" + email + "'";
    return await pool.query(query);
}

// SAFE example for comparison
async function safeGetUser(pool: Pool, userId: string): Promise<QueryResult> {
    // SAFE: Uses parameterized query
    return await pool.query(
        "SELECT * FROM users WHERE id = $1",
        [userId]
    );
}

export {
    getUserByName,
    searchProducts,
    deleteUser,
    updateEmail,
    getOrdersByDate,
    findUserByEmail,
    safeGetUser,
};
