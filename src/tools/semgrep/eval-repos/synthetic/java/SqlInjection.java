/**
 * Test file for SQL injection vulnerability detection.
 * Contains multiple SQL injection patterns.
 */

package smells.security;

import java.sql.*;

public class SqlInjection {

    // SQL INJECTION: String concatenation in SQL query
    public ResultSet getUserByName(Connection conn, String username) throws SQLException {
        String query = "SELECT * FROM users WHERE username = '" + username + "'";
        Statement stmt = conn.createStatement();
        return stmt.executeQuery(query);
    }

    // SQL INJECTION: String format in SQL query
    public void deleteUser(Connection conn, String userId) throws SQLException {
        String query = String.format("DELETE FROM users WHERE id = %s", userId);
        Statement stmt = conn.createStatement();
        stmt.executeUpdate(query);
    }

    // SQL INJECTION: Multiple injectable parameters
    public ResultSet searchProducts(Connection conn, String name, String category) throws SQLException {
        String query = "SELECT * FROM products WHERE name LIKE '%" + name + "%' AND category = '" + category + "'";
        Statement stmt = conn.createStatement();
        return stmt.executeQuery(query);
    }

    // SQL INJECTION: StringBuilder with user input
    public ResultSet getOrdersByDate(Connection conn, String startDate, String endDate) throws SQLException {
        StringBuilder sb = new StringBuilder();
        sb.append("SELECT * FROM orders WHERE created_at BETWEEN '");
        sb.append(startDate);
        sb.append("' AND '");
        sb.append(endDate);
        sb.append("'");
        Statement stmt = conn.createStatement();
        return stmt.executeQuery(sb.toString());
    }

    // SQL INJECTION: Using concat
    public void updateEmail(Connection conn, String userId, String email) throws SQLException {
        String query = "UPDATE users SET email = '".concat(email).concat("' WHERE id = ").concat(userId);
        Statement stmt = conn.createStatement();
        stmt.executeUpdate(query);
    }

    // SAFE: Parameterized query
    public ResultSet safeGetUser(Connection conn, int userId) throws SQLException {
        PreparedStatement pstmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
        pstmt.setInt(1, userId);
        return pstmt.executeQuery();
    }

    // SAFE: Another parameterized query
    public void safeUpdateEmail(Connection conn, int userId, String email) throws SQLException {
        PreparedStatement pstmt = conn.prepareStatement("UPDATE users SET email = ? WHERE id = ?");
        pstmt.setString(1, email);
        pstmt.setInt(2, userId);
        pstmt.executeUpdate();
    }
}
