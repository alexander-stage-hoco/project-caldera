// Test file for DD smell D1_EMPTY_CATCH equivalent in Go.
// Contains multiple ignored error patterns.
package smells

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

// ReadFileContent ignores file errors
// D1_EMPTY_CATCH equivalent: Ignoring error return
func ReadFileContent(path string) string {
	data, _ := os.ReadFile(path) // BAD: error ignored with _
	return string(data)
}

// ParseJSON ignores parsing errors
// D1_EMPTY_CATCH equivalent: Ignoring JSON error
func ParseJSON(jsonStr string, v interface{}) {
	json.Unmarshal([]byte(jsonStr), v) // BAD: error not checked
}

// ProcessFile ignores multiple errors
// D1_EMPTY_CATCH equivalent: Multiple ignored errors
func ProcessFile(path string) string {
	file, _ := os.Open(path)            // BAD: error ignored
	defer file.Close()                   // Missing error check on Close
	data, _ := io.ReadAll(file)          // BAD: error ignored
	return string(data)
}

// FetchData ignores HTTP-like error
// D1_EMPTY_CATCH equivalent: Error silently ignored
func FetchData(url string) ([]byte, error) {
	result := make([]byte, 0)

	// Simulated fetch that could fail
	data, err := simulateFetch(url)
	if err != nil {
		// D1_EMPTY_CATCH: Error acknowledged but not handled
		return result, nil // Returns nil error, hiding the failure
	}

	return data, nil
}

// ProcessItems ignores errors in loop
// D1_EMPTY_CATCH equivalent: Errors ignored in loop
func ProcessItems(items []string) []string {
	results := make([]string, 0)
	for _, item := range items {
		processed, _ := processItem(item) // BAD: error ignored
		results = append(results, processed)
	}
	return results
}

// SaveData ignores write error
func SaveData(path string, data []byte) {
	os.WriteFile(path, data, 0644) // BAD: error completely ignored
}

// CORRECT: Proper error handling
func ReadFileContentCorrect(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("failed to read file %s: %w", path, err)
	}
	return string(data), nil
}

// CORRECT: Proper JSON error handling
func ParseJSONCorrect(jsonStr string, v interface{}) error {
	if err := json.Unmarshal([]byte(jsonStr), v); err != nil {
		return fmt.Errorf("failed to parse JSON: %w", err)
	}
	return nil
}

// Helper functions
func simulateFetch(url string) ([]byte, error) {
	return nil, nil
}

func processItem(item string) (string, error) {
	return item, nil
}
