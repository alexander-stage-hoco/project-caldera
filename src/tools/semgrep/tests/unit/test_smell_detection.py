"""Tests for smell detection logic and DD category mapping."""

import sys
from pathlib import Path

# Add scripts directory to path for importing smell_analyzer
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from smell_analyzer import (
    detect_language,
    map_rule_to_smell,
    RULE_TO_SMELL_MAP,
    SMELL_CATEGORIES,
)


class TestDetectLanguage:
    """Tests for the detect_language function."""

    def test_python_detection(self):
        """Test Python file detection."""
        assert detect_language("main.py") == "python"
        assert detect_language("src/utils/helper.py") == "python"
        assert detect_language("/absolute/path/script.py") == "python"

    def test_javascript_detection(self):
        """Test JavaScript file detection."""
        assert detect_language("app.js") == "javascript"
        assert detect_language("src/index.js") == "javascript"

    def test_typescript_detection(self):
        """Test TypeScript file detection."""
        assert detect_language("component.ts") == "typescript"
        assert detect_language("component.tsx") == "typescript"

    def test_csharp_detection(self):
        """Test C# file detection."""
        assert detect_language("Service.cs") == "csharp"
        assert detect_language("src/Controllers/HomeController.cs") == "csharp"

    def test_java_detection(self):
        """Test Java file detection."""
        assert detect_language("Handler.java") == "java"
        assert detect_language("com/example/Main.java") == "java"

    def test_go_detection(self):
        """Test Go file detection."""
        assert detect_language("main.go") == "go"
        assert detect_language("pkg/handler/handler.go") == "go"

    def test_rust_detection(self):
        """Test Rust file detection."""
        assert detect_language("lib.rs") == "rust"
        assert detect_language("src/main.rs") == "rust"

    def test_ruby_detection(self):
        """Test Ruby file detection."""
        assert detect_language("script.rb") == "ruby"
        assert detect_language("app/models/user.rb") == "ruby"

    def test_php_detection(self):
        """Test PHP file detection."""
        assert detect_language("index.php") == "php"
        assert detect_language("src/Controller.php") == "php"

    def test_unknown_extension(self):
        """Test unknown file extension returns 'unknown'."""
        assert detect_language("file.xyz") == "unknown"
        assert detect_language("README.md") == "unknown"
        assert detect_language("Makefile") == "unknown"

    def test_case_insensitive(self):
        """Test that extension matching is case-insensitive."""
        assert detect_language("main.PY") == "python"
        assert detect_language("app.JS") == "javascript"
        assert detect_language("Service.CS") == "csharp"


class TestMapRuleToSmell:
    """Tests for the map_rule_to_smell function."""

    def test_dd_prefixed_rules_with_metadata(self):
        """Test DD-prefixed rules with dd_smell_id metadata."""
        metadata = {
            "dd_smell_id": "D1_EMPTY_CATCH",
            "dd_category": "error_handling",
        }
        smell_id, category = map_rule_to_smell("DD-D1-EMPTY-CATCH-python", metadata)
        assert smell_id == "D1_EMPTY_CATCH"
        assert category == "error_handling"

    def test_dd_prefixed_rules_without_metadata(self):
        """Test DD-prefixed rules without metadata use pattern matching."""
        smell_id, category = map_rule_to_smell("DD-D1-EMPTY-CATCH-python", None)
        assert smell_id == "D1_EMPTY_CATCH"
        assert category == "error_handling"

    def test_security_sql_injection_rules(self):
        """Test SQL injection rule mapping."""
        rules = ["sql-injection", "formatted-sql", "SCS0002", "CA3001", "CWE-89"]
        for rule in rules:
            smell_id, category = map_rule_to_smell(rule, None)
            assert smell_id == "SQL_INJECTION", f"Failed for rule: {rule}"
            assert category == "security", f"Failed for rule: {rule}"

    def test_security_xss_rules(self):
        """Test XSS rule mapping."""
        rules = ["xss", "cross-site-scripting", "SCS0029", "CWE-79"]
        for rule in rules:
            smell_id, category = map_rule_to_smell(rule, None)
            assert smell_id == "XSS_VULNERABILITY", f"Failed for rule: {rule}"
            assert category == "security", f"Failed for rule: {rule}"

    def test_security_path_traversal_rules(self):
        """Test path traversal rule mapping."""
        rules = ["path-traversal", "directory-traversal", "SCS0013", "CWE-22"]
        for rule in rules:
            smell_id, category = map_rule_to_smell(rule, None)
            assert smell_id == "PATH_TRAVERSAL", f"Failed for rule: {rule}"
            assert category == "security", f"Failed for rule: {rule}"

    def test_error_handling_rules(self):
        """Test error handling smell mapping."""
        rule_to_expected = {
            "empty-catch": "D1_EMPTY_CATCH",
            "bare-except": "D1_EMPTY_CATCH",
            "pass-in-except": "D1_EMPTY_CATCH",
            "generic-exception-caught": "D2_CATCH_ALL",
            "catch-broad-exception": "D2_CATCH_ALL",
        }
        for rule, expected_smell in rule_to_expected.items():
            smell_id, category = map_rule_to_smell(rule, None)
            assert smell_id == expected_smell, f"Failed for rule: {rule}"
            assert category == "error_handling", f"Failed for rule: {rule}"

    def test_async_concurrency_rules(self):
        """Test async/concurrency smell mapping."""
        rule_to_expected = {
            "async-void": "E2_ASYNC_VOID",
            "task-wait": "E1_SYNC_OVER_ASYNC",
            "task-result": "E1_SYNC_OVER_ASYNC",
        }
        for rule, expected_smell in rule_to_expected.items():
            smell_id, category = map_rule_to_smell(rule, None)
            assert smell_id == expected_smell, f"Failed for rule: {rule}"
            assert category == "async_concurrency", f"Failed for rule: {rule}"

    def test_resource_management_rules(self):
        """Test resource management smell mapping."""
        smell_id, category = map_rule_to_smell("httpclient-new", None)
        assert smell_id == "F3_HTTPCLIENT_NEW"
        assert category == "resource_management"

    def test_ca_deserialization_rules(self):
        """Test Microsoft CA deserialization rule mapping."""
        ca_rules = [
            "CA2300", "CA2301", "CA2302", "CA2305", "CA2310",
            "CA2321", "CA2326", "CA2327", "CA2328"
        ]
        for rule in ca_rules:
            smell_id, category = map_rule_to_smell(rule, None)
            assert smell_id == "UNSAFE_DESERIALIZATION", f"Failed for rule: {rule}"
            assert category == "security", f"Failed for rule: {rule}"

    def test_ca_crypto_rules(self):
        """Test Microsoft CA cryptography rule mapping."""
        ca_rules = ["CA5350", "CA5351", "CA5358", "CA5364", "CA5384", "CA5385"]
        for rule in ca_rules:
            smell_id, category = map_rule_to_smell(rule, None)
            assert smell_id == "INSECURE_CRYPTO", f"Failed for rule: {rule}"
            assert category == "security", f"Failed for rule: {rule}"

    def test_code_quality_rules(self):
        """Test code quality rule mapping (Phase 3)."""
        rule_to_expected = {
            "mutable-default-argument": ("H5_HIDDEN_DEPENDENCIES", "api_design"),
            "useless-comparison": ("I2_UNREACHABLE_CODE", "dead_code"),
            "unreachable-code": ("I2_UNREACHABLE_CODE", "dead_code"),
            "unused-variable": ("I1_UNUSED_IMPORT", "dead_code"),
        }
        for rule, (expected_smell, expected_cat) in rule_to_expected.items():
            smell_id, category = map_rule_to_smell(rule, None)
            assert smell_id == expected_smell, f"Failed for rule: {rule}"
            assert category == expected_cat, f"Failed for rule: {rule}"

    def test_unknown_rule_returns_rule_id(self):
        """Test unknown rules return the rule ID itself."""
        smell_id, category = map_rule_to_smell("completely-unknown-rule", None)
        assert smell_id == "completely-unknown-rule"
        assert category == "unknown"

    def test_default_fallback_for_exception_rules(self):
        """Test default fallback for rules containing 'exception'."""
        smell_id, category = map_rule_to_smell("some-exception-handler", None)
        assert smell_id == "D1_EMPTY_CATCH"
        assert category == "error_handling"

    def test_default_fallback_for_async_rules(self):
        """Test default fallback for rules containing 'async'."""
        smell_id, category = map_rule_to_smell("some-async-pattern", None)
        assert smell_id == "E2_ASYNC_VOID"
        assert category == "async_concurrency"


class TestSmellCategories:
    """Tests for SMELL_CATEGORIES mapping consistency."""

    def test_all_error_handling_smells_mapped(self):
        """Test all error handling smells have correct category."""
        error_smells = [
            "D1_EMPTY_CATCH", "D2_CATCH_ALL", "D3_LOG_AND_CONTINUE",
            "D4_INCORRECT_RETHROW", "D5_GENERIC_EXCEPTION", "D7_CATCH_RETURN_DEFAULT"
        ]
        for smell in error_smells:
            assert SMELL_CATEGORIES.get(smell) == "error_handling", f"Failed for: {smell}"

    def test_all_async_smells_mapped(self):
        """Test all async/concurrency smells have correct category."""
        async_smells = [
            "E1_SYNC_OVER_ASYNC", "E2_ASYNC_VOID", "E3_MISSING_CONFIGURE_AWAIT",
            "E4_MISSING_CANCELLATION", "E5_UNSAFE_LOCK", "E7_ASYNC_WITHOUT_AWAIT"
        ]
        for smell in async_smells:
            assert SMELL_CATEGORIES.get(smell) == "async_concurrency", f"Failed for: {smell}"

    def test_all_security_smells_mapped(self):
        """Test all security smells have correct category."""
        security_smells = [
            "SQL_INJECTION", "XSS_VULNERABILITY", "PATH_TRAVERSAL",
            "XXE_VULNERABILITY", "UNSAFE_DESERIALIZATION", "HARDCODED_SECRET",
            "INSECURE_CRYPTO", "COMMAND_INJECTION", "LDAP_INJECTION",
            "XPATH_INJECTION", "CSRF_VULNERABILITY", "OPEN_REDIRECT",
            "SSRF_VULNERABILITY", "BROKEN_ACCESS_CONTROL", "CODE_INJECTION",
            "SECURITY_MISCONFIGURATION", "INFORMATION_DISCLOSURE"
        ]
        for smell in security_smells:
            assert SMELL_CATEGORIES.get(smell) == "security", f"Failed for: {smell}"

    def test_rule_to_smell_map_consistency(self):
        """Test all mapped smells exist in SMELL_CATEGORIES."""
        for rule, smell_id in RULE_TO_SMELL_MAP.items():
            assert smell_id in SMELL_CATEGORIES, (
                f"Rule '{rule}' maps to '{smell_id}' which is not in SMELL_CATEGORIES"
            )
