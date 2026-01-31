/**
 * Test file for SQL injection vulnerability detection.
 * Contains multiple SQL injection patterns.
 */

const mysql = require('mysql2');

async function getUserByName(connection, username) {
    // SQL INJECTION: Template literal in SQL query
    const query = `SELECT * FROM users WHERE username = '${username}'`;
    const [rows] = await connection.execute(query);
    return rows[0];
}

async function searchProducts(connection, searchTerm) {
    // SQL INJECTION: String concatenation in SQL query
    const query = "SELECT * FROM products WHERE name LIKE '%" + searchTerm + "%'";
    const [rows] = await connection.execute(query);
    return rows;
}

async function deleteUser(connection, userId) {
    // SQL INJECTION: Direct string interpolation
    await connection.execute("DELETE FROM users WHERE id = " + userId);
}

async function updateEmail(connection, userId, email) {
    // SQL INJECTION: Multiple injectable parameters
    const query = `UPDATE users SET email = '${email}' WHERE id = ${userId}`;
    await connection.execute(query);
}

async function getOrdersByDate(connection, startDate, endDate) {
    // SQL INJECTION: String interpolation with multiple params
    const query = `SELECT * FROM orders WHERE created_at BETWEEN '${startDate}' AND '${endDate}'`;
    const [rows] = await connection.execute(query);
    return rows;
}

async function findUserByEmail(connection, email) {
    // SQL INJECTION: eval-like construction
    const query = "SELECT * FROM users WHERE email = '" + email + "'";
    const [rows] = await connection.execute(query);
    return rows[0];
}

// SAFE example for comparison
async function safeGetUser(connection, userId) {
    // SAFE: Uses parameterized query
    const [rows] = await connection.execute(
        "SELECT * FROM users WHERE id = ?",
        [userId]
    );
    return rows[0];
}

module.exports = {
    getUserByName,
    searchProducts,
    deleteUser,
    updateEmail,
    getOrdersByDate,
    findUserByEmail,
    safeGetUser,
};
