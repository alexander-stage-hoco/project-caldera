package com.example.security;

import java.sql.*;
import java.io.*;
import java.util.*;

/**
 * User service with intentional security vulnerabilities for testing.
 * DO NOT USE IN PRODUCTION.
 */
public class UserService {

    // Hardcoded credentials - security vulnerability
    private static final String DB_PASSWORD = "admin123";
    private static final String API_KEY = "sk-1234567890abcdef";

    private Connection connection;

    public UserService() throws SQLException {
        // Hardcoded connection string with credentials
        this.connection = DriverManager.getConnection(
            "jdbc:mysql://localhost:3306/users",
            "root",
            DB_PASSWORD
        );
    }

    /**
     * SQL Injection vulnerability - user input directly concatenated into query.
     */
    public User findUserByName(String username) throws SQLException {
        // VULNERABILITY: SQL Injection
        String query = "SELECT * FROM users WHERE username = '" + username + "'";
        Statement stmt = connection.createStatement();
        ResultSet rs = stmt.executeQuery(query);

        if (rs.next()) {
            return new User(
                rs.getInt("id"),
                rs.getString("username"),
                rs.getString("email")
            );
        }
        return null;
    }

    /**
     * Another SQL Injection vulnerability.
     */
    public List<User> searchUsers(String searchTerm, String sortColumn) throws SQLException {
        // VULNERABILITY: SQL Injection in both WHERE and ORDER BY
        String query = "SELECT * FROM users WHERE name LIKE '%" + searchTerm + "%' ORDER BY " + sortColumn;
        Statement stmt = connection.createStatement();
        ResultSet rs = stmt.executeQuery(query);

        List<User> users = new ArrayList<>();
        while (rs.next()) {
            users.add(new User(
                rs.getInt("id"),
                rs.getString("username"),
                rs.getString("email")
            ));
        }
        return users;
    }

    /**
     * Path traversal vulnerability.
     */
    public String readUserFile(String filename) throws IOException {
        // VULNERABILITY: Path traversal - user can access any file
        File file = new File("/app/uploads/" + filename);
        BufferedReader reader = new BufferedReader(new FileReader(file));
        StringBuilder content = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            content.append(line).append("\n");
        }
        reader.close();
        return content.toString();
    }

    /**
     * Command injection vulnerability.
     */
    public String runDiagnostics(String hostParam) throws IOException {
        // VULNERABILITY: Command injection
        String command = "ping -c 4 " + hostParam;
        Process process = Runtime.getRuntime().exec(command);

        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        StringBuilder output = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            output.append(line).append("\n");
        }
        return output.toString();
    }

    /**
     * Insecure deserialization - placeholder.
     */
    public Object deserializeData(byte[] data) throws IOException, ClassNotFoundException {
        // VULNERABILITY: Insecure deserialization
        ByteArrayInputStream bis = new ByteArrayInputStream(data);
        ObjectInputStream ois = new ObjectInputStream(bis);
        return ois.readObject();
    }
}

class User {
    private int id;
    private String username;
    private String email;

    public User(int id, String username, String email) {
        this.id = id;
        this.username = username;
        this.email = email;
    }

    public int getId() { return id; }
    public String getUsername() { return username; }
    public String getEmail() { return email; }
}
