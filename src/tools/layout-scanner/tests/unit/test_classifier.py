"""
Unit tests for classifier.py
"""

import pytest
from scripts.classifier import (
    classify_file,
    detect_language,
    classify_directory,
    classify_directory_by_name,
    get_classification_distribution,
    get_language_distribution,
    ClassificationResult,
    LanguageResult,
    CLASSIFICATIONS,
    PATH_RULES,
    FILENAME_RULES,
    EXTENSION_RULES,
    LANGUAGE_MAP,
    DIRECTORY_NAME_RULES,
)


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""

    def test_classification_result_fields(self):
        """ClassificationResult should have all required fields."""
        result = ClassificationResult(
            category="source",
            confidence=0.9,
            reason="extension:.py",
            signals={"extension": "source"},
        )
        assert result.category == "source"
        assert result.confidence == 0.9
        assert result.reason == "extension:.py"
        assert result.signals == {"extension": "source"}

    def test_classification_result_default_signals(self):
        """ClassificationResult should have empty signals by default."""
        result = ClassificationResult(
            category="test",
            confidence=0.8,
            reason="path:tests/",
        )
        assert result.signals == {}


class TestLanguageResult:
    """Tests for LanguageResult dataclass."""

    def test_language_result_fields(self):
        """LanguageResult should have all required fields."""
        result = LanguageResult(language="python", confidence=0.95)
        assert result.language == "python"
        assert result.confidence == 0.95


class TestClassifyFilePathRules:
    """Tests for path-based classification."""

    def test_vendor_path_node_modules(self):
        """node_modules/ should be classified as vendor."""
        result = classify_file(
            path="node_modules/lodash/index.js",
            name="index.js",
            extension=".js",
        )
        assert result.category == "vendor"
        assert "path:" in result.reason

    def test_vendor_path_vendor_dir(self):
        """vendor/ should be classified as vendor."""
        result = classify_file(
            path="vendor/github.com/pkg/errors/errors.go",
            name="errors.go",
            extension=".go",
        )
        assert result.category == "vendor"

    def test_vendor_path_third_party(self):
        """third_party/ should be classified as vendor."""
        result = classify_file(
            path="third_party/protobuf/src/google/protobuf.h",
            name="protobuf.h",
            extension=".h",
        )
        assert result.category == "vendor"

    def test_test_path_tests(self):
        """tests/ should be classified as test."""
        result = classify_file(
            path="tests/unit/test_main.py",
            name="test_main.py",
            extension=".py",
        )
        assert result.category == "test"

    def test_test_path_dunder_tests(self):
        """__tests__/ should be classified as test."""
        result = classify_file(
            path="src/components/__tests__/Button.test.js",
            name="Button.test.js",
            extension=".js",
        )
        assert result.category == "test"

    def test_test_path_spec(self):
        """spec/ should be classified as test."""
        result = classify_file(
            path="spec/models/user_spec.rb",
            name="user_spec.rb",
            extension=".rb",
        )
        assert result.category == "test"

    def test_docs_path(self):
        """docs/ should be classified as docs."""
        result = classify_file(
            path="docs/api/getting-started.md",
            name="getting-started.md",
            extension=".md",
        )
        assert result.category == "docs"

    def test_generated_path_dist(self):
        """dist/ should be classified as generated."""
        result = classify_file(
            path="dist/bundle.js",
            name="bundle.js",
            extension=".js",
        )
        assert result.category == "generated"

    def test_generated_path_build(self):
        """build/ should be classified as generated."""
        result = classify_file(
            path="build/output/app.js",
            name="app.js",
            extension=".js",
        )
        assert result.category == "generated"

    def test_generated_path_pycache(self):
        """__pycache__/ should be classified as generated."""
        result = classify_file(
            path="src/__pycache__/module.cpython-39.pyc",
            name="module.cpython-39.pyc",
            extension=".pyc",
        )
        assert result.category == "generated"

    def test_ci_path_github(self):
        """.github/ should be classified as ci."""
        result = classify_file(
            path=".github/workflows/ci.yml",
            name="ci.yml",
            extension=".yml",
        )
        assert result.category == "ci"

    def test_ci_path_gitlab(self):
        """.gitlab-ci/ should be classified as ci."""
        result = classify_file(
            path=".gitlab-ci/deploy.yml",
            name="deploy.yml",
            extension=".yml",
        )
        assert result.category == "ci"

    def test_config_path_vscode(self):
        """.vscode/ should be classified as config."""
        result = classify_file(
            path=".vscode/settings.json",
            name="settings.json",
            extension=".json",
        )
        assert result.category == "config"


class TestClassifyFileFilenamePatterns:
    """Tests for filename pattern classification."""

    def test_python_test_prefix(self):
        """test_*.py should be classified as test."""
        result = classify_file(
            path="src/test_utils.py",
            name="test_utils.py",
            extension=".py",
        )
        assert result.category == "test"

    def test_python_test_suffix(self):
        """*_test.py should be classified as test."""
        result = classify_file(
            path="src/utils_test.py",
            name="utils_test.py",
            extension=".py",
        )
        assert result.category == "test"

    def test_js_test_file(self):
        """*.test.js should be classified as test."""
        result = classify_file(
            path="src/App.test.js",
            name="App.test.js",
            extension=".js",
        )
        assert result.category == "test"

    def test_ts_spec_file(self):
        """*.spec.ts should be classified as test."""
        result = classify_file(
            path="src/service.spec.ts",
            name="service.spec.ts",
            extension=".ts",
        )
        assert result.category == "test"

    def test_csharp_test_file(self):
        """*Tests.cs should be classified as test."""
        result = classify_file(
            path="Tests/ServiceTests.cs",
            name="ServiceTests.cs",
            extension=".cs",
        )
        assert result.category == "test"

    def test_go_test_file(self):
        """*_test.go should be classified as test."""
        result = classify_file(
            path="pkg/handler_test.go",
            name="handler_test.go",
            extension=".go",
        )
        assert result.category == "test"

    def test_conftest_py(self):
        """conftest.py should be classified as test."""
        result = classify_file(
            path="conftest.py",
            name="conftest.py",
            extension=".py",
        )
        assert result.category == "test"

    def test_generated_g_cs(self):
        """*.g.cs should be classified as generated."""
        result = classify_file(
            path="Generated/Parser.g.cs",
            name="Parser.g.cs",
            extension=".cs",
        )
        assert result.category == "generated"

    def test_generated_min_js(self):
        """*.min.js should be classified as generated."""
        result = classify_file(
            path="assets/app.min.js",
            name="app.min.js",
            extension=".js",
        )
        assert result.category == "generated"

    def test_generated_d_ts(self):
        """*.d.ts should be classified as generated."""
        result = classify_file(
            path="types/index.d.ts",
            name="index.d.ts",
            extension=".ts",
        )
        assert result.category == "generated"

    def test_generated_package_lock(self):
        """package-lock.json should be classified as generated."""
        result = classify_file(
            path="package-lock.json",
            name="package-lock.json",
            extension=".json",
        )
        assert result.category == "generated"

    def test_generated_yarn_lock(self):
        """yarn.lock should be classified as generated."""
        result = classify_file(
            path="yarn.lock",
            name="yarn.lock",
            extension=".lock",
        )
        assert result.category == "generated"

    def test_config_eslintrc(self):
        """.eslintrc should be classified as config."""
        result = classify_file(
            path=".eslintrc",
            name=".eslintrc",
            extension="",
        )
        assert result.category == "config"

    def test_config_makefile(self):
        """Makefile should be classified as config."""
        result = classify_file(
            path="Makefile",
            name="Makefile",
            extension="",
        )
        assert result.category == "config"

    def test_config_dockerfile(self):
        """Dockerfile should be classified as config."""
        result = classify_file(
            path="Dockerfile",
            name="Dockerfile",
            extension="",
        )
        assert result.category == "config"

    def test_config_docker_compose(self):
        """docker-compose.yml should be classified as config."""
        result = classify_file(
            path="docker-compose.yml",
            name="docker-compose.yml",
            extension=".yml",
        )
        assert result.category == "config"

    def test_config_tsconfig(self):
        """tsconfig.json should be classified as config."""
        result = classify_file(
            path="tsconfig.json",
            name="tsconfig.json",
            extension=".json",
        )
        assert result.category == "config"

    def test_docs_readme(self):
        """README.md should be classified as docs."""
        result = classify_file(
            path="README.md",
            name="README.md",
            extension=".md",
        )
        assert result.category == "docs"

    def test_docs_license(self):
        """LICENSE should be classified as docs."""
        result = classify_file(
            path="LICENSE",
            name="LICENSE",
            extension="",
        )
        assert result.category == "docs"

    def test_docs_changelog(self):
        """CHANGELOG.md should be classified as docs."""
        result = classify_file(
            path="CHANGELOG.md",
            name="CHANGELOG.md",
            extension=".md",
        )
        assert result.category == "docs"

    def test_ci_travis_yml(self):
        """.travis.yml should be classified as ci."""
        result = classify_file(
            path=".travis.yml",
            name=".travis.yml",
            extension=".yml",
        )
        assert result.category == "ci"


class TestClassifyFileExtensionRules:
    """Tests for extension-based classification."""

    def test_config_json(self):
        """Standalone .json files can be classified as config."""
        result = classify_file(
            path="config.json",
            name="config.json",
            extension=".json",
        )
        # config signal is weak, may be overridden by other signals
        assert "extension:.json" in result.signals or result.category == "config"

    def test_config_yaml(self):
        """Standalone .yaml files can be classified as config."""
        result = classify_file(
            path="settings.yaml",
            name="settings.yaml",
            extension=".yaml",
        )
        assert "extension:.yaml" in result.signals or result.category == "config"

    def test_config_toml(self):
        """Standalone .toml files can be classified as config."""
        result = classify_file(
            path="pyproject.toml",
            name="pyproject.toml",
            extension=".toml",
        )
        assert "extension:.toml" in result.signals or result.category == "config"

    def test_config_tf_terraform(self):
        """.tf files should be classified as config."""
        result = classify_file(
            path="infra/main.tf",
            name="main.tf",
            extension=".tf",
        )
        assert result.category == "config"

    def test_config_csproj(self):
        """.csproj files should be classified as config."""
        result = classify_file(
            path="MyProject.csproj",
            name="MyProject.csproj",
            extension=".csproj",
        )
        assert result.category == "config"

    def test_config_sln(self):
        """.sln files should be classified as config."""
        result = classify_file(
            path="Solution.sln",
            name="Solution.sln",
            extension=".sln",
        )
        assert result.category == "config"

    def test_docs_md(self):
        """.md files should be classified as docs."""
        result = classify_file(
            path="notes.md",
            name="notes.md",
            extension=".md",
        )
        assert result.category == "docs"

    def test_docs_rst(self):
        """.rst files should be classified as docs."""
        result = classify_file(
            path="guide.rst",
            name="guide.rst",
            extension=".rst",
        )
        assert result.category == "docs"


class TestClassifyFileDefaultBehavior:
    """Tests for default classification behavior."""

    def test_source_file_default(self):
        """Regular source files should be classified as source."""
        result = classify_file(
            path="src/main.py",
            name="main.py",
            extension=".py",
        )
        assert result.category == "source"

    def test_unknown_extension_defaults_to_source(self):
        """Unknown extensions should default to source."""
        result = classify_file(
            path="data.xyz",
            name="data.xyz",
            extension=".xyz",
        )
        assert result.category == "source"

    def test_empty_extension(self):
        """Files without extension should still be classifiable."""
        result = classify_file(
            path="script",
            name="script",
            extension="",
        )
        assert result.category in CLASSIFICATIONS


class TestClassifyFileCustomRules:
    """Tests for custom classification rules."""

    def test_custom_path_rule(self):
        """Custom path rules should be applied."""
        result = classify_file(
            path="myvendor/lib.py",
            name="lib.py",
            extension=".py",
            custom_path_rules={"vendor": ["myvendor/"]},
        )
        assert result.category == "vendor"

    def test_custom_filename_rule(self):
        """Custom filename rules should be applied."""
        result = classify_file(
            path="benchmark_utils.py",
            name="benchmark_utils.py",
            extension=".py",
            custom_filename_rules={"test": [r"^benchmark_.*\.py$"]},
        )
        assert result.category == "test"

    def test_override_takes_precedence(self):
        """Overrides should take precedence over other rules."""
        result = classify_file(
            path="tests/integration/test_api.py",
            name="test_api.py",
            extension=".py",
            overrides={"tests/integration/": "source"},
        )
        assert result.category == "source"
        assert result.confidence == 1.0
        assert "override" in result.reason


class TestClassifyFileConfidence:
    """Tests for classification confidence scores."""

    def test_path_signal_high_confidence(self):
        """Path-based matches should have high confidence."""
        result = classify_file(
            path="node_modules/lodash/index.js",
            name="index.js",
            extension=".js",
        )
        assert result.confidence >= 0.5

    def test_filename_signal_medium_confidence(self):
        """Filename-based matches should have medium confidence."""
        result = classify_file(
            path="src/test_utils.py",
            name="test_utils.py",
            extension=".py",
        )
        assert result.confidence >= 0.4

    def test_extension_only_lower_confidence(self):
        """Extension-only matches should have lower confidence."""
        result = classify_file(
            path="config.json",
            name="config.json",
            extension=".json",
        )
        # Extension-only gives lower confidence
        assert result.confidence <= 0.6

    def test_default_low_confidence(self):
        """Default classification should have low confidence."""
        result = classify_file(
            path="unknown.xyz",
            name="unknown.xyz",
            extension=".xyz",
        )
        assert result.confidence <= 0.3

    def test_multiple_signals_increase_confidence(self):
        """Multiple matching signals should increase confidence."""
        # Path + filename + extension all point to test
        result = classify_file(
            path="tests/test_api.py",
            name="test_api.py",
            extension=".py",
        )
        assert result.confidence >= 0.6


class TestDetectLanguage:
    """Tests for language detection."""

    def test_python_language(self):
        """.py should detect as python."""
        result = detect_language("main.py", ".py")
        assert result.language == "python"
        assert result.confidence >= 0.9

    def test_python_pyi(self):
        """.pyi should detect as python."""
        result = detect_language("types.pyi", ".pyi")
        assert result.language == "python"

    def test_javascript_language(self):
        """.js should detect as javascript."""
        result = detect_language("app.js", ".js")
        assert result.language == "javascript"

    def test_typescript_language(self):
        """.ts should detect as typescript."""
        result = detect_language("service.ts", ".ts")
        assert result.language == "typescript"

    def test_tsx_language(self):
        """.tsx should detect as typescript."""
        result = detect_language("Component.tsx", ".tsx")
        assert result.language == "typescript"

    def test_csharp_language(self):
        """.cs should detect as csharp."""
        result = detect_language("Program.cs", ".cs")
        assert result.language == "csharp"

    def test_go_language(self):
        """.go should detect as go."""
        result = detect_language("main.go", ".go")
        assert result.language == "go"

    def test_rust_language(self):
        """.rs should detect as rust."""
        result = detect_language("lib.rs", ".rs")
        assert result.language == "rust"

    def test_java_language(self):
        """.java should detect as java."""
        result = detect_language("Main.java", ".java")
        assert result.language == "java"

    def test_kotlin_language(self):
        """.kt should detect as kotlin."""
        result = detect_language("App.kt", ".kt")
        assert result.language == "kotlin"

    def test_ruby_language(self):
        """.rb should detect as ruby."""
        result = detect_language("app.rb", ".rb")
        assert result.language == "ruby"

    def test_cpp_language(self):
        """.cpp should detect as cpp."""
        result = detect_language("main.cpp", ".cpp")
        assert result.language == "cpp"

    def test_c_language(self):
        """.c should detect as c."""
        result = detect_language("main.c", ".c")
        assert result.language == "c"

    def test_shell_language(self):
        """.sh should detect as shell."""
        result = detect_language("script.sh", ".sh")
        assert result.language == "shell"

    def test_hcl_terraform(self):
        """.tf should detect as hcl."""
        result = detect_language("main.tf", ".tf")
        assert result.language == "hcl"

    def test_yaml_language(self):
        """.yaml should detect as yaml."""
        result = detect_language("config.yaml", ".yaml")
        assert result.language == "yaml"

    def test_json_language(self):
        """.json should detect as json."""
        result = detect_language("data.json", ".json")
        assert result.language == "json"

    def test_markdown_language(self):
        """.md should detect as markdown."""
        result = detect_language("README.md", ".md")
        assert result.language == "markdown"

    def test_makefile_by_name(self):
        """Makefile should detect as makefile."""
        result = detect_language("Makefile", "")
        assert result.language == "makefile"

    def test_dockerfile_by_name(self):
        """Dockerfile should detect as dockerfile."""
        result = detect_language("Dockerfile", "")
        assert result.language == "dockerfile"

    def test_unknown_extension(self):
        """Unknown extension should return unknown."""
        result = detect_language("file.xyz", ".xyz")
        assert result.language == "unknown"
        assert result.confidence == 0.0

    def test_case_insensitive(self):
        """Extension detection should be case insensitive."""
        result = detect_language("Main.PY", ".PY")
        assert result.language == "python"


class TestClassifyDirectory:
    """Tests for directory classification."""

    def test_empty_directory(self):
        """Empty directory should classify as other."""
        category, reason = classify_directory([])
        assert category == "other"
        assert "empty" in reason.lower()

    def test_single_classification(self):
        """Single file should determine directory classification."""
        category, reason = classify_directory(["source"])
        assert category == "source"

    def test_majority_vote(self):
        """Directory should use majority vote."""
        files = ["source", "source", "source", "test", "config"]
        category, reason = classify_directory(files)
        assert category == "source"
        assert "majority" in reason

    def test_majority_percentage_in_reason(self):
        """Reason should include percentage."""
        files = ["test", "test", "test", "source"]
        category, reason = classify_directory(files)
        assert category == "test"
        assert "75%" in reason

    def test_tie_breaks_alphabetically(self):
        """Ties should be broken deterministically."""
        files = ["source", "test"]
        category, reason = classify_directory(files)
        # max() with same count will pick one consistently
        assert category in ["source", "test"]

    def test_all_same_classification(self):
        """All same classification should give 100%."""
        files = ["vendor"] * 10
        category, reason = classify_directory(files)
        assert category == "vendor"
        assert "100%" in reason


class TestGetClassificationDistribution:
    """Tests for classification distribution function."""

    def test_empty_list(self):
        """Empty list should return empty distribution."""
        dist = get_classification_distribution([])
        assert dist == {}

    def test_single_classification(self):
        """Single classification should have count 1."""
        dist = get_classification_distribution(["source"])
        assert dist == {"source": 1}

    def test_multiple_classifications(self):
        """Multiple classifications should be counted."""
        files = ["source", "source", "test", "config", "test"]
        dist = get_classification_distribution(files)
        assert dist == {"source": 2, "test": 2, "config": 1}

    def test_all_same_classification(self):
        """All same should have one key with total count."""
        files = ["vendor"] * 5
        dist = get_classification_distribution(files)
        assert dist == {"vendor": 5}


class TestGetLanguageDistribution:
    """Tests for language distribution function."""

    def test_empty_list(self):
        """Empty list should return empty distribution."""
        dist = get_language_distribution([])
        assert dist == {}

    def test_single_language(self):
        """Single language should have count 1."""
        dist = get_language_distribution(["python"])
        assert dist == {"python": 1}

    def test_multiple_languages(self):
        """Multiple languages should be counted."""
        langs = ["python", "python", "typescript", "go"]
        dist = get_language_distribution(langs)
        assert dist == {"python": 2, "typescript": 1, "go": 1}

    def test_unknown_excluded(self):
        """Unknown language should be excluded."""
        langs = ["python", "unknown", "unknown", "go"]
        dist = get_language_distribution(langs)
        assert dist == {"python": 1, "go": 1}
        assert "unknown" not in dist

    def test_all_unknown(self):
        """All unknown should return empty distribution."""
        dist = get_language_distribution(["unknown"] * 5)
        assert dist == {}


class TestClassifyFileEdgeCases:
    """Tests for edge cases in file classification."""

    def test_path_normalization_backslash(self):
        """Backslashes should be normalized."""
        result = classify_file(
            path="node_modules\\lodash\\index.js",
            name="index.js",
            extension=".js",
        )
        assert result.category == "vendor"

    def test_case_insensitive_path(self):
        """Path matching should be case insensitive."""
        result = classify_file(
            path="NODE_MODULES/lodash/index.js",
            name="index.js",
            extension=".js",
        )
        assert result.category == "vendor"

    def test_deeply_nested_path(self):
        """Classification should work for deeply nested paths."""
        result = classify_file(
            path="a/b/c/d/e/f/tests/unit/test_main.py",
            name="test_main.py",
            extension=".py",
        )
        assert result.category == "test"

    def test_multiple_signals_same_category(self):
        """Multiple signals for same category should work."""
        # Path + filename both say test
        result = classify_file(
            path="tests/test_api.py",
            name="test_api.py",
            extension=".py",
        )
        assert result.category == "test"
        # Should have multiple signals
        test_signals = [k for k, v in result.signals.items() if v == "test"]
        assert len(test_signals) >= 2

    def test_conflicting_signals(self):
        """Highest scoring category should win with conflicting signals."""
        # test_*.py in vendor/ - path wins (0.9) over filename (0.8)
        result = classify_file(
            path="vendor/test_helper.py",
            name="test_helper.py",
            extension=".py",
        )
        # Path signal is stronger, but both signals contribute
        # The actual winner depends on the exact score accumulation
        assert result.category in ["vendor", "test"]

    def test_unicode_path(self):
        """Unicode paths should be handled."""
        result = classify_file(
            path="docs/日本語/readme.md",
            name="readme.md",
            extension=".md",
        )
        assert result.category == "docs"

    def test_special_characters_in_name(self):
        """Special characters in filename should be handled."""
        result = classify_file(
            path="src/app[v2].py",
            name="app[v2].py",
            extension=".py",
        )
        assert result.category == "source"

    def test_empty_path(self):
        """Empty path should still classify based on filename/extension."""
        result = classify_file(
            path="",
            name="test_main.py",
            extension=".py",
        )
        assert result.category == "test"


class TestConstantsIntegrity:
    """Tests to verify classification constants are properly defined."""

    def test_classifications_list_populated(self):
        """CLASSIFICATIONS list should have expected categories."""
        expected = ["source", "test", "config", "generated", "docs", "vendor", "build", "ci", "vcs", "other"]
        for cat in expected:
            assert cat in CLASSIFICATIONS

    def test_path_rules_categories_valid(self):
        """PATH_RULES categories should be in CLASSIFICATIONS."""
        for category in PATH_RULES:
            assert category in CLASSIFICATIONS

    def test_filename_rules_categories_valid(self):
        """FILENAME_RULES categories should be in CLASSIFICATIONS."""
        for category in FILENAME_RULES:
            assert category in CLASSIFICATIONS

    def test_extension_rules_categories_valid(self):
        """EXTENSION_RULES categories should be in CLASSIFICATIONS."""
        for category in EXTENSION_RULES:
            assert category in CLASSIFICATIONS

    def test_language_map_populated(self):
        """LANGUAGE_MAP should have common languages."""
        common_extensions = [".py", ".js", ".ts", ".cs", ".go", ".rs", ".java"]
        for ext in common_extensions:
            assert ext in LANGUAGE_MAP


class TestSecurityPatternFix:
    """Tests for SECURITY filename pattern fix (Issue 1.1)."""

    def test_security_py_not_classified_as_docs(self):
        """security_issues.py should NOT be classified as docs."""
        result = classify_file(
            path="src/security_issues.py",
            name="security_issues.py",
            extension=".py",
        )
        assert result.category != "docs"
        assert result.category == "source"

    def test_security_md_classified_as_docs(self):
        """SECURITY.md should be classified as docs."""
        result = classify_file(
            path="SECURITY.md",
            name="SECURITY.md",
            extension=".md",
        )
        assert result.category == "docs"

    def test_security_txt_classified_as_docs(self):
        """SECURITY.txt should be classified as docs."""
        result = classify_file(
            path="SECURITY.txt",
            name="SECURITY.txt",
            extension=".txt",
        )
        assert result.category == "docs"

    def test_security_no_extension_classified_as_docs(self):
        """SECURITY (no extension) should be classified as docs."""
        result = classify_file(
            path="SECURITY",
            name="SECURITY",
            extension="",
        )
        assert result.category == "docs"

    def test_security_rst_classified_as_docs(self):
        """SECURITY.rst should be classified as docs."""
        result = classify_file(
            path="SECURITY.rst",
            name="SECURITY.rst",
            extension=".rst",
        )
        assert result.category == "docs"


class TestVcsClassification:
    """Tests for VCS (version control system) classification (Issue 1.3-1.4)."""

    def test_vcs_in_classifications(self):
        """VCS should be in CLASSIFICATIONS list."""
        assert "vcs" in CLASSIFICATIONS

    def test_git_directory_classified_as_vcs(self):
        """Files in .git/ should be classified as vcs."""
        result = classify_file(
            path=".git/config",
            name="config",
            extension="",
        )
        assert result.category == "vcs"

    def test_git_objects_classified_as_vcs(self):
        """Files in .git/objects/ should be classified as vcs."""
        result = classify_file(
            path=".git/objects/ab/cd1234",
            name="cd1234",
            extension="",
        )
        assert result.category == "vcs"

    def test_svn_directory_classified_as_vcs(self):
        """Files in .svn/ should be classified as vcs."""
        result = classify_file(
            path=".svn/entries",
            name="entries",
            extension="",
        )
        assert result.category == "vcs"

    def test_hg_directory_classified_as_vcs(self):
        """Files in .hg/ should be classified as vcs."""
        result = classify_file(
            path=".hg/hgrc",
            name="hgrc",
            extension="",
        )
        assert result.category == "vcs"


class TestShellScriptClassification:
    """Tests for shell script classification (Issue 1.2)."""

    def test_sh_file_classified_as_config(self):
        """build.sh should be classified as config."""
        result = classify_file(
            path="scripts/build.sh",
            name="build.sh",
            extension=".sh",
        )
        assert result.category == "config"

    def test_bash_file_classified_as_config(self):
        """.bash file should be classified as config."""
        result = classify_file(
            path="setup.bash",
            name="setup.bash",
            extension=".bash",
        )
        assert result.category == "config"

    def test_ps1_file_classified_as_config(self):
        """PowerShell .ps1 should be classified as config."""
        result = classify_file(
            path="deploy.ps1",
            name="deploy.ps1",
            extension=".ps1",
        )
        assert result.category == "config"

    def test_bat_file_classified_as_config(self):
        """Windows .bat should be classified as config."""
        result = classify_file(
            path="build.bat",
            name="build.bat",
            extension=".bat",
        )
        assert result.category == "config"


class TestImageFileClassification:
    """Tests for image file classification (Issue 1.2)."""

    def test_png_classified_as_other(self):
        """logo.png should be classified as other."""
        result = classify_file(
            path="assets/logo.png",
            name="logo.png",
            extension=".png",
        )
        assert result.category == "other"

    def test_jpg_classified_as_other(self):
        """photo.jpg should be classified as other."""
        result = classify_file(
            path="images/photo.jpg",
            name="photo.jpg",
            extension=".jpg",
        )
        assert result.category == "other"

    def test_svg_classified_as_other(self):
        """icon.svg should be classified as other."""
        result = classify_file(
            path="assets/icon.svg",
            name="icon.svg",
            extension=".svg",
        )
        assert result.category == "other"

    def test_ico_classified_as_other(self):
        """favicon.ico should be classified as other."""
        result = classify_file(
            path="favicon.ico",
            name="favicon.ico",
            extension=".ico",
        )
        assert result.category == "other"


class TestJenkinsfileClassification:
    """Tests for Jenkinsfile CI classification (Issue: classification reasoning)."""

    def test_jenkinsfile_classified_as_ci(self):
        """Jenkinsfile should be classified as ci, not config."""
        result = classify_file(
            path="Jenkinsfile",
            name="Jenkinsfile",
            extension="",
        )
        assert result.category == "ci"
        assert "filename:" in result.reason

    def test_jenkinsfile_in_subdirectory(self):
        """Jenkinsfile in subdirectory should be classified as ci."""
        result = classify_file(
            path="ci/Jenkinsfile",
            name="Jenkinsfile",
            extension="",
        )
        assert result.category == "ci"


class TestDependencyFileClassification:
    """Tests for dependency file classification (Issue: classification reasoning)."""

    def test_requirements_txt_classified_as_config(self):
        """requirements.txt should be classified as config, not docs."""
        result = classify_file(
            path="requirements.txt",
            name="requirements.txt",
            extension=".txt",
        )
        assert result.category == "config"
        assert "filename:" in result.reason

    def test_requirements_dev_txt_classified_as_config(self):
        """requirements-dev.txt should be classified as config."""
        result = classify_file(
            path="requirements-dev.txt",
            name="requirements-dev.txt",
            extension=".txt",
        )
        assert result.category == "config"

    def test_go_mod_classified_as_config(self):
        """go.mod should be classified as config, not source."""
        result = classify_file(
            path="go.mod",
            name="go.mod",
            extension=".mod",
        )
        assert result.category == "config"
        assert "filename:" in result.reason

    def test_go_sum_classified_as_config(self):
        """go.sum should be classified as config, not generated."""
        result = classify_file(
            path="go.sum",
            name="go.sum",
            extension=".sum",
        )
        assert result.category == "config"
        assert "filename:" in result.reason

    def test_ndproj_classified_as_config(self):
        """NDepend .ndproj files should be classified as config."""
        result = classify_file(
            path="MyProject.ndproj",
            name="MyProject.ndproj",
            extension=".ndproj",
        )
        assert result.category == "config"


class TestSourceExtensionReasoning:
    """Tests for source extension reasoning (Issue: classification reasoning)."""

    def test_python_file_has_extension_reason(self):
        """.py files should have extension-based reason, not default."""
        result = classify_file(
            path="src/main.py",
            name="main.py",
            extension=".py",
        )
        assert result.category == "source"
        assert "extension:.py" in result.signals
        assert "default" not in result.reason

    def test_typescript_file_has_extension_reason(self):
        """.ts files should have extension-based reason."""
        result = classify_file(
            path="src/app.ts",
            name="app.ts",
            extension=".ts",
        )
        assert result.category == "source"
        assert "extension:.ts" in result.signals

    def test_rust_file_has_extension_reason(self):
        """.rs files should have extension-based reason."""
        result = classify_file(
            path="src/lib.rs",
            name="lib.rs",
            extension=".rs",
        )
        assert result.category == "source"
        assert "extension:.rs" in result.signals

    def test_go_file_has_extension_reason(self):
        """.go files should have extension-based reason."""
        result = classify_file(
            path="main.go",
            name="main.go",
            extension=".go",
        )
        assert result.category == "source"
        assert "extension:.go" in result.signals

    def test_csharp_file_has_extension_reason(self):
        """.cs files should have extension-based reason."""
        result = classify_file(
            path="Program.cs",
            name="Program.cs",
            extension=".cs",
        )
        assert result.category == "source"
        assert "extension:.cs" in result.signals

    def test_java_file_has_extension_reason(self):
        """.java files should have extension-based reason."""
        result = classify_file(
            path="Main.java",
            name="Main.java",
            extension=".java",
        )
        assert result.category == "source"
        assert "extension:.java" in result.signals


class TestSrcDirectoryPathBoost:
    """Tests for src/ directory confidence boost (Phase 2 improvement)."""

    def test_src_directory_boosts_confidence(self):
        """Files in src/ should have higher confidence than extension-only."""
        # File in src/ directory
        result_src = classify_file(
            path="src/rust/main.rs",
            name="main.rs",
            extension=".rs",
        )
        # File with only extension signal
        result_ext_only = classify_file(
            path="main.rs",
            name="main.rs",
            extension=".rs",
        )
        assert result_src.category == "source"
        assert result_ext_only.category == "source"
        # src/ path should boost confidence
        assert result_src.confidence > result_ext_only.confidence
        assert "path:src/" in result_src.signals

    def test_src_path_pattern_matches(self):
        """src/ path pattern should match various source file types."""
        test_cases = [
            ("src/main.py", "main.py", ".py"),
            ("src/app/index.ts", "index.ts", ".ts"),
            ("src/lib/utils.go", "utils.go", ".go"),
            ("src/rust/lib.rs", "lib.rs", ".rs"),
        ]
        for path, name, ext in test_cases:
            result = classify_file(path=path, name=name, extension=ext)
            assert result.category == "source", f"Failed for {path}"
            assert "path:src/" in result.signals, f"No path signal for {path}"

    def test_app_path_pattern_matches(self):
        """app/ path pattern should match source files."""
        result = classify_file(
            path="app/models/user.py",
            name="user.py",
            extension=".py",
        )
        assert result.category == "source"
        assert "path:app/" in result.signals

    def test_internal_path_pattern_matches(self):
        """internal/ path pattern should match source files (Go convention)."""
        result = classify_file(
            path="internal/pkg/handler.go",
            name="handler.go",
            extension=".go",
        )
        assert result.category == "source"
        assert "path:internal/" in result.signals

    def test_cmd_path_pattern_matches(self):
        """cmd/ path pattern should match source files (Go convention)."""
        result = classify_file(
            path="cmd/server/main.go",
            name="main.go",
            extension=".go",
        )
        assert result.category == "source"
        assert "path:cmd/" in result.signals

    def test_pkg_not_a_source_pattern(self):
        """pkg/ is NOT a source pattern to avoid conflicts with vendor paths.

        Paths like vendor/github.com/pkg/ would incorrectly match if pkg/
        were a source pattern. Instead, pkg/ files are classified via extension.
        """
        result = classify_file(
            path="pkg/utils/helpers.go",
            name="helpers.go",
            extension=".go",
        )
        assert result.category == "source"
        # pkg/ should NOT be in signals - classification is via extension only
        assert "path:pkg/" not in result.signals
        assert "extension:.go" in result.signals


class TestTypeScriptDeclarationFiles:
    """Tests for TypeScript .d.ts file classification."""

    def test_dts_files_classified_as_generated(self):
        """.d.ts files should be classified as generated (TypeScript declarations)."""
        result = classify_file(
            path="src/types.d.ts",
            name="types.d.ts",
            extension=".ts",
        )
        # .d.ts files are classified as generated by filename pattern
        assert result.category == "generated"
        assert "filename:" in result.reason

    def test_dts_in_types_directory(self):
        """types.d.ts in a types directory should be generated."""
        result = classify_file(
            path="types/index.d.ts",
            name="index.d.ts",
            extension=".ts",
        )
        assert result.category == "generated"

    def test_dts_ambient_module(self):
        """Ambient module declarations (.d.ts) should be generated."""
        result = classify_file(
            path="global.d.ts",
            name="global.d.ts",
            extension=".ts",
        )
        assert result.category == "generated"

    def test_generated_dts_in_dist(self):
        """.d.ts files in dist/ should be generated (both path and filename match)."""
        result = classify_file(
            path="dist/index.d.ts",
            name="index.d.ts",
            extension=".ts",
        )
        assert result.category == "generated"


class TestConfidenceCalibration:
    """Tests for confidence calibration with well-known config files (Phase 3)."""

    def test_cargo_toml_high_confidence(self):
        """Cargo.toml should have confidence >= 0.5 via filename pattern."""
        result = classify_file(path="Cargo.toml", name="Cargo.toml", extension=".toml")
        assert result.category == "config"
        assert result.confidence >= 0.5
        assert "filename:" in result.reason

    def test_pyproject_toml_high_confidence(self):
        """pyproject.toml should have confidence >= 0.5 via filename pattern."""
        result = classify_file(path="pyproject.toml", name="pyproject.toml", extension=".toml")
        assert result.category == "config"
        assert result.confidence >= 0.5
        assert "filename:" in result.reason

    def test_package_json_high_confidence(self):
        """package.json should have confidence >= 0.5 via filename pattern."""
        result = classify_file(path="package.json", name="package.json", extension=".json")
        assert result.category == "config"
        assert result.confidence >= 0.5
        assert "filename:" in result.reason

    def test_composer_json_high_confidence(self):
        """composer.json should have confidence >= 0.5 via filename pattern."""
        result = classify_file(path="composer.json", name="composer.json", extension=".json")
        assert result.category == "config"
        assert result.confidence >= 0.5
        assert "filename:" in result.reason

    def test_setup_cfg_high_confidence(self):
        """setup.cfg should have confidence >= 0.5 via filename pattern."""
        result = classify_file(path="setup.cfg", name="setup.cfg", extension=".cfg")
        assert result.category == "config"
        assert result.confidence >= 0.5
        assert "filename:" in result.reason

    def test_setup_py_high_confidence(self):
        """setup.py should have confidence >= 0.5 via filename pattern."""
        result = classify_file(path="setup.py", name="setup.py", extension=".py")
        assert result.category == "config"
        assert result.confidence >= 0.5
        assert "filename:" in result.reason

    def test_tox_ini_high_confidence(self):
        """tox.ini should have confidence >= 0.5 via filename pattern."""
        result = classify_file(path="tox.ini", name="tox.ini", extension=".ini")
        assert result.category == "config"
        assert result.confidence >= 0.5
        assert "filename:" in result.reason

    def test_gemfile_high_confidence(self):
        """Gemfile should have confidence >= 0.5 via filename pattern."""
        result = classify_file(path="Gemfile", name="Gemfile", extension="")
        assert result.category == "config"
        assert result.confidence >= 0.5
        assert "filename:" in result.reason

    def test_build_gradle_high_confidence(self):
        """build.gradle should have confidence >= 0.5 via filename pattern."""
        result = classify_file(path="build.gradle", name="build.gradle", extension=".gradle")
        assert result.category == "config"
        assert result.confidence >= 0.5
        assert "filename:" in result.reason

    def test_pom_xml_high_confidence(self):
        """pom.xml should have confidence >= 0.5 via filename pattern."""
        result = classify_file(path="pom.xml", name="pom.xml", extension=".xml")
        assert result.category == "config"
        assert result.confidence >= 0.5
        assert "filename:" in result.reason


class TestDirectoryNameHeuristics:
    """Tests for directory name-based classification heuristics (Phase 3)."""

    def test_src_directory_always_source(self):
        """src/ directory should be 'source' regardless of content."""
        category, reason = classify_directory_by_name("src", ["generated", "generated", "generated"])
        assert category == "source"
        assert "directory_name" in reason

    def test_lib_directory_always_source(self):
        """lib/ directory should be 'source' regardless of content."""
        category, reason = classify_directory_by_name("lib", ["generated", "config"])
        assert category == "source"
        assert "directory_name" in reason

    def test_pkg_directory_always_source(self):
        """pkg/ directory should be 'source' regardless of content."""
        category, reason = classify_directory_by_name("pkg", ["test", "test"])
        assert category == "source"
        assert "directory_name" in reason

    def test_app_directory_always_source(self):
        """app/ directory should be 'source' regardless of content."""
        category, reason = classify_directory_by_name("app", ["config", "docs"])
        assert category == "source"
        assert "directory_name" in reason

    def test_internal_directory_always_source(self):
        """internal/ directory should be 'source' (Go convention)."""
        category, reason = classify_directory_by_name("internal", ["generated"])
        assert category == "source"
        assert "directory_name" in reason

    def test_cmd_directory_always_source(self):
        """cmd/ directory should be 'source' (Go convention)."""
        category, reason = classify_directory_by_name("cmd", ["generated"])
        assert category == "source"
        assert "directory_name" in reason

    def test_build_directory_always_generated(self):
        """build/ directory should be 'generated' regardless of content."""
        category, reason = classify_directory_by_name("build", ["source", "source"])
        assert category == "generated"
        assert "directory_name" in reason

    def test_dist_directory_always_generated(self):
        """dist/ directory should be 'generated' regardless of content."""
        category, reason = classify_directory_by_name("dist", ["source"])
        assert category == "generated"
        assert "directory_name" in reason

    def test_target_directory_always_generated(self):
        """target/ directory should be 'generated' (Rust/Java convention)."""
        category, reason = classify_directory_by_name("target", ["source"])
        assert category == "generated"
        assert "directory_name" in reason

    def test_bin_directory_always_generated(self):
        """bin/ directory should be 'generated'."""
        category, reason = classify_directory_by_name("bin", ["source"])
        assert category == "generated"
        assert "directory_name" in reason

    def test_obj_directory_always_generated(self):
        """obj/ directory should be 'generated' (.NET convention)."""
        category, reason = classify_directory_by_name("obj", ["source"])
        assert category == "generated"
        assert "directory_name" in reason

    def test_tests_directory_always_test(self):
        """tests/ directory should be 'test' regardless of content."""
        category, reason = classify_directory_by_name("tests", ["source", "config"])
        assert category == "test"
        assert "directory_name" in reason

    def test_test_directory_always_test(self):
        """test/ directory should be 'test' regardless of content."""
        category, reason = classify_directory_by_name("test", ["source"])
        assert category == "test"
        assert "directory_name" in reason

    def test_spec_directory_always_test(self):
        """spec/ directory should be 'test' (Ruby/JS convention)."""
        category, reason = classify_directory_by_name("spec", ["source"])
        assert category == "test"
        assert "directory_name" in reason

    def test_dunder_tests_directory_always_test(self):
        """__tests__/ directory should be 'test' (Jest convention)."""
        category, reason = classify_directory_by_name("__tests__", ["source"])
        assert category == "test"
        assert "directory_name" in reason

    def test_docs_directory_always_docs(self):
        """docs/ directory should be 'docs' regardless of content."""
        category, reason = classify_directory_by_name("docs", ["source", "config"])
        assert category == "docs"
        assert "directory_name" in reason

    def test_doc_directory_always_docs(self):
        """doc/ directory should be 'docs'."""
        category, reason = classify_directory_by_name("doc", ["source"])
        assert category == "docs"
        assert "directory_name" in reason

    def test_vendor_directory_always_vendor(self):
        """vendor/ directory should be 'vendor' regardless of content."""
        category, reason = classify_directory_by_name("vendor", ["source", "source"])
        assert category == "vendor"
        assert "directory_name" in reason

    def test_node_modules_directory_always_vendor(self):
        """node_modules/ directory should be 'vendor'."""
        category, reason = classify_directory_by_name("node_modules", ["source"])
        assert category == "vendor"
        assert "directory_name" in reason

    def test_github_directory_always_ci(self):
        """.github/ directory should be 'ci' regardless of content."""
        category, reason = classify_directory_by_name(".github", ["config"])
        assert category == "ci"
        assert "directory_name" in reason

    def test_unknown_directory_uses_majority(self):
        """Unknown directory names should fall back to majority vote."""
        category, reason = classify_directory_by_name("mydir", ["test", "test", "source"])
        assert category == "test"
        assert "majority" in reason

    def test_empty_directory_classification(self):
        """Empty directory with unknown name should be 'other'."""
        category, reason = classify_directory_by_name("mydir", [])
        assert category == "other"
        assert "empty" in reason.lower()

    def test_case_insensitive_directory_names(self):
        """Directory name matching should be case insensitive."""
        # Test uppercase
        category, reason = classify_directory_by_name("SRC", ["generated"])
        assert category == "source"

        # Test mixed case
        category, reason = classify_directory_by_name("Tests", ["source"])
        assert category == "test"

        # Test mixed case for node_modules
        category, reason = classify_directory_by_name("Node_Modules", ["source"])
        assert category == "vendor"


class TestDirectoryNameRulesConstant:
    """Tests for DIRECTORY_NAME_RULES constant integrity."""

    def test_directory_name_rules_has_expected_categories(self):
        """DIRECTORY_NAME_RULES should have expected categories."""
        expected = ["source", "test", "docs", "generated", "vendor", "ci"]
        for cat in expected:
            assert cat in DIRECTORY_NAME_RULES

    def test_directory_name_rules_categories_valid(self):
        """DIRECTORY_NAME_RULES categories should be in CLASSIFICATIONS."""
        for category in DIRECTORY_NAME_RULES:
            assert category in CLASSIFICATIONS

    def test_source_directory_names_populated(self):
        """Source directory names should include common conventions."""
        names = DIRECTORY_NAME_RULES["source"]
        assert "src" in names
        assert "lib" in names
        assert "app" in names

    def test_test_directory_names_populated(self):
        """Test directory names should include common conventions."""
        names = DIRECTORY_NAME_RULES["test"]
        assert "test" in names
        assert "tests" in names
        assert "__tests__" in names

    def test_generated_directory_names_populated(self):
        """Generated directory names should include common conventions."""
        names = DIRECTORY_NAME_RULES["generated"]
        assert "build" in names
        assert "dist" in names
        assert "target" in names


class TestNdprojLanguageDetection:
    """Tests for .ndproj language detection (Phase 3)."""

    def test_ndproj_language_detection(self):
        """.ndproj files should detect as xml."""
        result = detect_language("MyProject.ndproj", ".ndproj")
        assert result.language == "xml"

    def test_ndproj_in_language_map(self):
        """.ndproj should be in LANGUAGE_MAP."""
        assert ".ndproj" in LANGUAGE_MAP
        assert LANGUAGE_MAP[".ndproj"] == "xml"


class TestEmptyDirectoryWithKnownName:
    """Tests for empty directories with well-known names (Phase 3.1)."""

    def test_empty_build_directory_is_generated(self):
        """Empty build/ directory should be 'generated' based on name."""
        category, reason = classify_directory_by_name("build", [])
        assert category == "generated"
        assert "directory_name" in reason

    def test_empty_dist_directory_is_generated(self):
        """Empty dist/ directory should be 'generated' based on name."""
        category, reason = classify_directory_by_name("dist", [])
        assert category == "generated"
        assert "directory_name" in reason

    def test_empty_out_directory_is_generated(self):
        """Empty out/ directory should be 'generated' based on name."""
        category, reason = classify_directory_by_name("out", [])
        assert category == "generated"
        assert "directory_name" in reason

    def test_empty_src_directory_is_source(self):
        """Empty src/ directory should be 'source' based on name."""
        category, reason = classify_directory_by_name("src", [])
        assert category == "source"
        assert "directory_name" in reason

    def test_empty_tests_directory_is_test(self):
        """Empty tests/ directory should be 'test' based on name."""
        category, reason = classify_directory_by_name("tests", [])
        assert category == "test"
        assert "directory_name" in reason

    def test_empty_unknown_directory_is_other(self):
        """Empty directory with unknown name should be 'other'."""
        category, reason = classify_directory_by_name("mydir", [])
        assert category == "other"
        assert "empty" in reason.lower()
