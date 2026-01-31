/**
 * Test file for DD smell D1_EMPTY_CATCH detection.
 * Contains multiple empty catch blocks.
 */

package smells.errorhandling;

import java.io.*;
import java.sql.*;

public class EmptyCatch {

    // D1_EMPTY_CATCH: Empty catch block
    public String readFileContent(String path) {
        try {
            return new String(java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(path)));
        } catch (FileNotFoundException e) {
            // Empty catch - swallows exception
        } catch (IOException e) {
            // Another empty catch
        }
        return "";
    }

    // D1_EMPTY_CATCH: Generic exception with empty body
    public Object parseJson(String json) {
        try {
            // Simulated JSON parsing
            return json;
        } catch (Exception e) {
            // Silently ignore errors
        }
        return null;
    }

    // D1_EMPTY_CATCH: Multiple empty catches
    public void processData(Object data) {
        try {
            validateData(data);
            transformData(data);
            saveData(data);
        } catch (IllegalArgumentException e) {
        } catch (IllegalStateException e) {
        } catch (Exception e) {
        }
    }

    // D1_EMPTY_CATCH in loop
    public void processItems(String[] items) {
        for (String item : items) {
            try {
                processItem(item);
            } catch (Exception e) {
                // Empty catch in loop
            }
        }
    }

    // D1_EMPTY_CATCH: SQL exception swallowed
    public ResultSet executeQuery(Connection conn, String query) {
        try {
            Statement stmt = conn.createStatement();
            return stmt.executeQuery(query);
        } catch (SQLException e) {
            // Dangerous: SQL errors silently ignored
        }
        return null;
    }

    private void validateData(Object data) {}
    private void transformData(Object data) {}
    private void saveData(Object data) {}
    private void processItem(String item) {}
}
