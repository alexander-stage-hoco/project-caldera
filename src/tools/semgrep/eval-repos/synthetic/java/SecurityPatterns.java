/**
 * Test file for Java security vulnerability detection.
 * Contains patterns detected by p/java ruleset.
 */
package synthetic.java;

import java.io.*;
import java.sql.*;
import javax.servlet.http.*;
import javax.xml.parsers.*;
import org.xml.sax.InputSource;

public class SecurityPatterns {

    // SQL_INJECTION: JDBC concatenation
    public ResultSet unsafeJdbcQuery(Connection conn, String userId) throws SQLException {
        String query = "SELECT * FROM users WHERE id = " + userId;
        Statement stmt = conn.createStatement();
        return stmt.executeQuery(query);
    }

    // SQL_INJECTION: String format in query
    public ResultSet unsafeFormattedQuery(Connection conn, String name) throws SQLException {
        String query = String.format("SELECT * FROM users WHERE name = '%s'", name);
        Statement stmt = conn.createStatement();
        return stmt.executeQuery(query);
    }

    // COMMAND_INJECTION: Runtime.exec with user input
    public Process unsafeRuntimeExec(String command) throws IOException {
        Runtime runtime = Runtime.getRuntime();
        return runtime.exec(command);
    }

    // COMMAND_INJECTION: ProcessBuilder with user input
    public Process unsafeProcessBuilder(String command) throws IOException {
        ProcessBuilder pb = new ProcessBuilder(command);
        return pb.start();
    }

    // UNSAFE_DESERIALIZATION: ObjectInputStream
    public Object unsafeDeserialization(InputStream input) throws Exception {
        ObjectInputStream ois = new ObjectInputStream(input);
        return ois.readObject();
    }

    // XXE_VULNERABILITY: DocumentBuilder without security features
    public void unsafeXmlParsing(String xml) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        DocumentBuilder builder = factory.newDocumentBuilder();
        builder.parse(new InputSource(new StringReader(xml)));
    }

    // XSS_VULNERABILITY: Direct output to response
    public void unsafeXssOutput(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String name = req.getParameter("name");
        resp.getWriter().println("<h1>Hello " + name + "</h1>");
    }

    // INSECURE_CRYPTO: Weak random
    public int unsafeRandom() {
        java.util.Random random = new java.util.Random();
        return random.nextInt();
    }

    // INSECURE_CRYPTO: ECB mode
    public byte[] unsafeEcbMode(byte[] data, byte[] key) throws Exception {
        javax.crypto.Cipher cipher = javax.crypto.Cipher.getInstance("AES/ECB/PKCS5Padding");
        javax.crypto.spec.SecretKeySpec keySpec = new javax.crypto.spec.SecretKeySpec(key, "AES");
        cipher.init(javax.crypto.Cipher.ENCRYPT_MODE, keySpec);
        return cipher.doFinal(data);
    }

    // OPEN_REDIRECT: Redirect without validation
    public void unsafeRedirect(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String url = req.getParameter("redirect");
        resp.sendRedirect(url);
    }

    // SAFE: Parameterized query
    public ResultSet safeQuery(Connection conn, String userId) throws SQLException {
        String query = "SELECT * FROM users WHERE id = ?";
        PreparedStatement stmt = conn.prepareStatement(query);
        stmt.setString(1, userId);
        return stmt.executeQuery();
    }

    // SAFE: Secure random
    public int safeRandom() throws Exception {
        java.security.SecureRandom random = new java.security.SecureRandom();
        return random.nextInt();
    }

    // SAFE: CBC mode with IV
    public byte[] safeCbcMode(byte[] data, byte[] key, byte[] iv) throws Exception {
        javax.crypto.Cipher cipher = javax.crypto.Cipher.getInstance("AES/CBC/PKCS5Padding");
        javax.crypto.spec.SecretKeySpec keySpec = new javax.crypto.spec.SecretKeySpec(key, "AES");
        javax.crypto.spec.IvParameterSpec ivSpec = new javax.crypto.spec.IvParameterSpec(iv);
        cipher.init(javax.crypto.Cipher.ENCRYPT_MODE, keySpec, ivSpec);
        return cipher.doFinal(data);
    }
}
