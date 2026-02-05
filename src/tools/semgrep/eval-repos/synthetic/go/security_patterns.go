// Test file for Go security vulnerability detection.
// Contains patterns detected by p/go ruleset.
package synthetic

import (
	"crypto/md5"
	"crypto/tls"
	"database/sql"
	"fmt"
	"html/template"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
)

// SQL_INJECTION: String concatenation in SQL query
func UnsafeSqlQuery(db *sql.DB, userId string) (*sql.Rows, error) {
	query := "SELECT * FROM users WHERE id = " + userId
	return db.Query(query)
}

// SQL_INJECTION: fmt.Sprintf in SQL query
func UnsafeFormattedQuery(db *sql.DB, name string) (*sql.Rows, error) {
	query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", name)
	return db.Query(query)
}

// COMMAND_INJECTION: exec.Command with user input
func UnsafeExecCommand(userCommand string) ([]byte, error) {
	cmd := exec.Command("sh", "-c", userCommand)
	return cmd.Output()
}

// COMMAND_INJECTION: os.exec with shell
func UnsafeOsExec(command string) ([]byte, error) {
	return exec.Command(command).Output()
}

// XSS_VULNERABILITY: template without escaping
func UnsafeTemplateRender(w http.ResponseWriter, userInput string) {
	tmpl := template.Must(template.New("test").Parse("<h1>Hello " + userInput + "</h1>"))
	tmpl.Execute(w, nil)
}

// PATH_TRAVERSAL: filepath.Join with user input
func UnsafeFileRead(basePath, userPath string) ([]byte, error) {
	fullPath := filepath.Join(basePath, userPath)
	return ioutil.ReadFile(fullPath)
}

// PATH_TRAVERSAL: Direct file access with user input
func UnsafeDirectFileAccess(filename string) ([]byte, error) {
	return os.ReadFile(filename)
}

// INSECURE_CRYPTO: MD5 hashing
func UnsafeMd5Hash(data []byte) []byte {
	hash := md5.Sum(data)
	return hash[:]
}

// INSECURE_CRYPTO: TLS InsecureSkipVerify
func UnsafeTlsConfig() *tls.Config {
	return &tls.Config{
		InsecureSkipVerify: true,
	}
}

// INSECURE_CRYPTO: Weak random with math/rand
func UnsafeWeakRandom() int {
	return rand.Intn(100)
}

// SSRF_VULNERABILITY: HTTP request with user-controlled URL
func UnsafeSsrfRequest(userUrl string) (*http.Response, error) {
	return http.Get(userUrl)
}

// RESOURCE_LEAK: Defer in loop
func UnsafeDeferInLoop(files []string) {
	for _, f := range files {
		file, _ := os.Open(f)
		defer file.Close() // RESOURCE_LEAK: defer in loop
	}
}

// SAFE: Parameterized query
func SafeSqlQuery(db *sql.DB, userId string) (*sql.Rows, error) {
	return db.Query("SELECT * FROM users WHERE id = ?", userId)
}

// SAFE: Proper template escaping
func SafeTemplateRender(w http.ResponseWriter, userInput string) {
	tmpl := template.Must(template.New("test").Parse("<h1>Hello {{.}}</h1>"))
	tmpl.Execute(w, template.HTMLEscapeString(userInput))
}

// SAFE: Crypto-secure random
import "crypto/rand"

func SafeSecureRandom() ([]byte, error) {
	b := make([]byte, 32)
	_, err := rand.Read(b)
	return b, err
}

// SAFE: Proper TLS config
func SafeTlsConfig() *tls.Config {
	return &tls.Config{
		MinVersion: tls.VersionTLS12,
	}
}
