package synthetic;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;

/**
 * Java file with error handling anti-patterns for testing D5_GENERIC_EXCEPTION detection.
 */
public class GenericException {

    // D5_GENERIC_EXCEPTION: Throwing generic Exception
    public void badThrowGeneric(String filename) throws Exception {
        if (filename == null) {
            throw new Exception("Filename cannot be null");
        }
        processFile(filename);
    }

    // D5_GENERIC_EXCEPTION: Another generic throw
    public int parseWithGenericException(String value) throws Exception {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            throw new Exception("Failed to parse: " + value);
        }
    }

    // D2_CATCH_ALL: Catching generic Exception
    public void catchAllExample() {
        try {
            riskyOperation();
        } catch (Exception e) {
            // D2_CATCH_ALL: Too broad
            System.out.println("Something went wrong");
        }
    }

    // GOOD: Specific exception
    public void goodThrowSpecific(String filename) throws IllegalArgumentException {
        if (filename == null) {
            throw new IllegalArgumentException("Filename cannot be null");
        }
        processFile(filename);
    }

    // GOOD: Specific catch
    public int goodParseWithSpecificException(String value) throws NumberFormatException {
        return Integer.parseInt(value);
    }

    private void processFile(String filename) {
        // File processing logic
    }

    private void riskyOperation() throws IOException {
        // Some I/O operation
    }
}
