"""
File Classifier for Layout Scanner.

Multi-signal classification engine that categorizes files based on:
- Path patterns (vendor/, test/, etc.)
- Filename patterns (test_*.py, *.spec.ts, etc.)
- Extension rules (.json, .md, etc.)
- Language detection (via go-enry with fallback to extension-based)

Provides confidence scores and human-readable explanations.
Supports configurable rules via YAML files.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .rule_loader import RuleSet

# Import enhanced language detection
try:
    # Try relative import first (when used as package)
    from .language_detector import (
        detect_language as _detect_language_enhanced,
        LanguageResult as _LanguageResult,
        is_binary_file,
        is_vendor_file as _is_vendor_file,
        is_generated_file as _is_generated_file,
        ENRY_AVAILABLE,
    )
    ENHANCED_DETECTION = True
except ImportError:
    try:
        # Try absolute import (when run directly)
        from language_detector import (
            detect_language as _detect_language_enhanced,
            LanguageResult as _LanguageResult,
            is_binary_file,
            is_vendor_file as _is_vendor_file,
            is_generated_file as _is_generated_file,
            ENRY_AVAILABLE,
        )
        ENHANCED_DETECTION = True
    except ImportError:
        ENHANCED_DETECTION = False
        ENRY_AVAILABLE = False

# Classification categories
CLASSIFICATIONS = [
    "source",     # Production source code
    "test",       # Test files and fixtures
    "config",     # Configuration files
    "generated",  # Auto-generated code
    "docs",       # Documentation
    "vendor",     # Third-party dependencies
    "build",      # Build artifacts
    "ci",         # CI/CD configuration
    "vcs",        # Version control system files
    "other",      # Unclassified
]

# Signal 1: Path-based rules (highest priority, weight 0.9)
# Note: Source patterns are matched at path start only to avoid conflicts
# with paths like "vendor/github.com/pkg/" or "third_party/protobuf/src/"
PATH_RULES: Dict[str, List[str]] = {
    "source": [
        "src/", "app/", "internal/", "cmd/",
    ],
    "vendor": [
        "vendor/", "node_modules/", "third_party/", "external/",
        "packages/", ".nuget/", "bower_components/", "jspm_packages/",
        "web_modules/", "lib/", "libs/",
    ],
    "test": [
        "tests/", "test/", "__tests__/", "spec/", "testing/",
        "test_fixtures/", "testdata/", "fixtures/", "e2e/",
        "integration/", "unit/", "__mocks__/", "mocks/",
    ],
    "docs": [
        "docs/", "documentation/", "doc/", "wiki/", "man/",
    ],
    "generated": [
        "generated/", "gen/", "dist/", "build/", "out/",
        ".next/", ".nuxt/", "target/", "bin/", "obj/",
        "_build/", "__pycache__/", ".cache/",
        ".scannerwork/", ".sonar/", ".coverage/", ".nyc_output/",
    ],
    "ci": [
        ".github/", ".gitlab-ci/", ".circleci/", ".travis/",
        ".azure-pipelines/", ".buildkite/", "jenkins/",
    ],
    "config": [
        ".vscode/", ".idea/", ".devcontainer/", ".husky/",
    ],
    "vcs": [
        ".git/", ".svn/", ".hg/", ".bzr/",
    ],
}

# Signal 2: Filename pattern rules (weight 0.8)
FILENAME_RULES: Dict[str, List[str]] = {
    "test": [
        r"^test_.*\.py$",           # Python: test_*.py
        r".*_test\.py$",            # Python: *_test.py
        r".*\.test\.[jt]sx?$",      # JS/TS: *.test.js, *.test.tsx
        r".*\.spec\.[jt]sx?$",      # JS/TS: *.spec.ts
        r".*Tests?\.cs$",           # C#: *Test.cs, *Tests.cs
        r".*Tests?\.java$",         # Java: *Test.java
        r".*_test\.go$",            # Go: *_test.go
        r".*_test\.rs$",            # Rust: *_test.rs
        r".*_spec\.rb$",            # Ruby: *_spec.rb
        r"^conftest\.py$",          # pytest fixtures
        r"^jest\.config\.[jt]s$",   # Jest config
        r"^vitest\.config\.[jt]s$", # Vitest config
    ],
    "generated": [
        r".*\.g\.cs$",              # C#: *.g.cs
        r".*\.generated\..*$",      # *.generated.*
        r".*\.min\.[jc]ss?$",       # *.min.js, *.min.css
        r".*\.bundle\.js$",         # *.bundle.js
        r".*\.d\.ts$",              # TypeScript declarations
        r".*_pb2\.py$",             # Protobuf Python
        r".*\.pb\.go$",             # Protobuf Go
        r".*_pb2_grpc\.py$",        # gRPC Python
        r".*\.designer\.cs$",       # Visual Studio designer
        r".*\.Designer\.cs$",       # Visual Studio designer (capital)
        r"^package-lock\.json$",    # npm lock file
        r"^yarn\.lock$",            # Yarn lock file
        r"^pnpm-lock\.yaml$",       # pnpm lock file
        r"^Pipfile\.lock$",         # Pipenv lock file
        r"^poetry\.lock$",          # Poetry lock file
        r"^Cargo\.lock$",           # Rust lock file
    ],
    "config": [
        r"^\..*rc$",                # .eslintrc, .prettierrc
        r"^\..*rc\.json$",          # .eslintrc.json
        r"^\..*rc\.ya?ml$",         # .eslintrc.yaml
        r"^\..*rc\.js$",            # .eslintrc.js
        r"^.*\.config\.[jt]s$",     # webpack.config.js
        r"^.*\.config\.mjs$",       # vite.config.mjs
        r"^Makefile$",
        r"^Dockerfile.*$",
        r"^docker-compose.*$",
        r"^Vagrantfile$",
        r"^Procfile$",
        r"^\.gitignore$",
        r"^\.gitattributes$",
        r"^\.gitmodules$",           # Git submodules config
        r"^\.editorconfig$",
        r"^\.env.*$",
        r"^tsconfig.*\.json$",
        r"^jsconfig.*\.json$",
        r"^babel\.config.*$",
        r"^webpack\..*$",
        r"^rollup\.config.*$",
        r"^vite\.config.*$",
        r"^turbo\.json$",
        r"^lerna\.json$",
        r"^nx\.json$",
        r"^angular\.json$",
        r"^nuxt\.config.*$",
        r"^next\.config.*$",
        # Dependency files
        r"^requirements.*\.txt$",   # Python dependencies
        r"^constraints.*\.txt$",    # Python constraints
        r"^go\.mod$",               # Go module file
        r"^go\.sum$",               # Go module checksums
        r".*\.ndproj$",             # NDepend project files
        # Project manifest files (high-confidence config)
        r"^pyproject\.toml$",       # Python project
        r"^Cargo\.toml$",           # Rust project
        r"^package\.json$",         # Node.js project
        r"^composer\.json$",        # PHP project
        r"^setup\.cfg$",            # Python setup
        r"^setup\.py$",             # Python setup script
        r"^tox\.ini$",              # Python testing
        r"^Gemfile$",               # Ruby bundler
        r"^build\.gradle$",         # Gradle build
        r"^pom\.xml$",              # Maven build
    ],
    "docs": [
        r"^README.*$",
        r"^CHANGELOG.*$",
        r"^CHANGES.*$",
        r"^HISTORY.*$",
        r"^CONTRIBUTING.*$",
        r"^LICENSE.*$",
        r"^LICENCE.*$",
        r"^AUTHORS.*$",
        r"^MAINTAINERS.*$",
        r"^CODE_OF_CONDUCT.*$",
        r"^SECURITY(\.(md|txt|rst|adoc))?$",
        r"^CLAUDE\.md$",
    ],
    "ci": [
        r"^\.travis\.ya?ml$",
        r"^\.gitlab-ci\.ya?ml$",
        r"^azure-pipelines\.ya?ml$",
        r"^cloudbuild\.ya?ml$",
        r"^bitbucket-pipelines\.ya?ml$",
        r"^appveyor\.ya?ml$",
        r"^\.drone\.ya?ml$",
        r"^Jenkinsfile$",
    ],
}

# Signal 3: Extension rules (weight 0.5)
EXTENSION_RULES: Dict[str, List[str]] = {
    "source": [
        # Python
        ".py", ".pyw", ".pyi", ".pyx",
        # JavaScript/TypeScript
        ".js", ".jsx", ".mjs", ".ts", ".tsx", ".mts",
        # C#
        ".cs",
        # Java/Kotlin
        ".java", ".kt", ".kts",
        # Go
        ".go",
        # Rust
        ".rs",
        # C/C++
        ".c", ".h", ".cpp", ".cc", ".hpp",
        # Ruby
        ".rb",
        # PHP
        ".php",
        # Swift
        ".swift",
        # Scala
        ".scala",
    ],
    "config": [
        ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
        ".conf", ".config", ".props", ".targets", ".env",
        ".properties", ".plist",
        # Infrastructure as Code
        ".tf", ".tfvars", ".hcl",
        # .NET project files
        ".csproj", ".fsproj", ".vbproj", ".sln", ".slnx",
        ".vcxproj", ".vcproj", ".esproj",
        # Shell scripts
        ".sh", ".bash", ".zsh", ".fish",
        # PowerShell
        ".ps1", ".psm1", ".psd1",
        # Windows batch
        ".bat", ".cmd",
    ],
    "docs": [
        ".md", ".rst", ".txt", ".adoc", ".asciidoc",
        ".tex", ".htm", ".html",
    ],
    "other": [
        # Images
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
        ".bmp", ".tiff", ".webp",
    ],
}

# Language detection from extensions
LANGUAGE_MAP: Dict[str, str] = {
    # Python
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    ".pyx": "python",
    ".pxd": "python",

    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",

    # C#
    ".cs": "csharp",
    ".csx": "csharp",

    # Java/Kotlin
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",

    # Go
    ".go": "go",

    # Rust
    ".rs": "rust",

    # C/C++
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",

    # Ruby
    ".rb": "ruby",
    ".rake": "ruby",
    ".gemspec": "ruby",

    # PHP
    ".php": "php",
    ".phtml": "php",

    # Swift
    ".swift": "swift",

    # Objective-C
    ".m": "objective-c",
    ".mm": "objective-c",

    # Shell
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".fish": "shell",

    # PowerShell
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".psd1": "powershell",

    # Scala
    ".scala": "scala",
    ".sc": "scala",

    # Elixir
    ".ex": "elixir",
    ".exs": "elixir",

    # Clojure
    ".clj": "clojure",
    ".cljs": "clojure",
    ".cljc": "clojure",

    # Haskell
    ".hs": "haskell",
    ".lhs": "haskell",

    # Lua
    ".lua": "lua",

    # Perl
    ".pl": "perl",
    ".pm": "perl",

    # R
    ".r": "r",
    ".R": "r",

    # SQL
    ".sql": "sql",

    # YAML
    ".yaml": "yaml",
    ".yml": "yaml",

    # JSON
    ".json": "json",
    ".jsonc": "json",
    ".json5": "json",

    # XML
    ".xml": "xml",
    ".xsl": "xml",
    ".xslt": "xml",
    ".xsd": "xml",
    ".xaml": "xaml",  # WPF/UWP/Avalonia markup

    # HTML
    ".html": "html",
    ".htm": "html",

    # CSS
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",

    # Markdown
    ".md": "markdown",
    ".markdown": "markdown",

    # TOML
    ".toml": "toml",

    # INI
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "ini",

    # HCL (Terraform, Packer, etc.)
    ".tf": "hcl",
    ".tfvars": "hcl",
    ".hcl": "hcl",

    # Dockerfile
    "Dockerfile": "dockerfile",

    # Makefile
    "Makefile": "makefile",

    # .NET project files (MSBuild)
    ".csproj": "msbuild",
    ".fsproj": "msbuild",
    ".vbproj": "msbuild",
    ".vcxproj": "msbuild",
    ".vcproj": "msbuild",
    ".esproj": "msbuild",
    ".props": "msbuild",
    ".targets": "msbuild",
    ".resx": "msbuild",

    # NuGet specification
    ".nuspec": "nuspec",

    # NDepend project files (XML-based)
    ".ndproj": "xml",
}


@dataclass
class ClassificationResult:
    """Result of classifying a file."""
    category: str                      # Primary classification
    confidence: float                  # 0.0 to 1.0
    reason: str                        # Human-readable explanation
    signals: Dict[str, str] = field(default_factory=dict)  # All signals that fired


@dataclass
class LanguageResult:
    """Result of detecting file language."""
    language: str                      # Detected language or "unknown"
    confidence: float                  # 0.0 to 1.0


def classify_file(
    path: str,
    name: str,
    extension: str,
    custom_path_rules: Optional[Dict[str, List[str]]] = None,
    custom_filename_rules: Optional[Dict[str, List[str]]] = None,
    custom_extension_rules: Optional[Dict[str, List[str]]] = None,
    overrides: Optional[Dict[str, str]] = None,
    rules: Optional["RuleSet"] = None,
    weights: Optional[Dict[str, float]] = None,
) -> ClassificationResult:
    """
    Classify a file using multi-signal approach.

    Args:
        path: Relative path from repository root
        name: Filename
        extension: File extension including dot
        custom_path_rules: Additional path-based rules
        custom_filename_rules: Additional filename pattern rules
        custom_extension_rules: Additional extension-based rules
        overrides: Path prefix -> category overrides
        rules: Optional RuleSet from rule_loader (if provided, uses these rules)
        weights: Optional custom weights (path, filename, extension)

    Returns:
        ClassificationResult with category, confidence, and explanation
    """
    scores: Dict[str, float] = defaultdict(float)
    signals: Dict[str, str] = {}

    # Determine signal weights
    if rules and rules.weights:
        w_path = rules.weights.get("path", 0.9)
        w_filename = rules.weights.get("filename", 0.8)
        w_extension = rules.weights.get("extension", 0.5)
    elif weights:
        w_path = weights.get("path", 0.9)
        w_filename = weights.get("filename", 0.8)
        w_extension = weights.get("extension", 0.5)
    else:
        w_path, w_filename, w_extension = 0.9, 0.8, 0.5

    # Check overrides first (highest priority)
    if overrides:
        for prefix, category in overrides.items():
            if path.startswith(prefix) or f"/{path}".startswith(f"/{prefix}"):
                return ClassificationResult(
                    category=category,
                    confidence=1.0,
                    reason=f"override:{prefix}",
                    signals={"override": category}
                )

    # Build path rules from sources
    if rules:
        path_rules = {**rules.path_rules}
    else:
        path_rules = {**PATH_RULES}
    if custom_path_rules:
        for cat, patterns in custom_path_rules.items():
            path_rules.setdefault(cat, []).extend(patterns)

    # Build filename rules from sources
    if rules:
        filename_rules = {**rules.filename_rules}
    else:
        filename_rules = {**FILENAME_RULES}
    if custom_filename_rules:
        for cat, patterns in custom_filename_rules.items():
            filename_rules.setdefault(cat, []).extend(patterns)

    # Build extension rules from sources
    if rules:
        extension_rules = {**rules.extension_rules}
    else:
        extension_rules = {**EXTENSION_RULES}
    if custom_extension_rules:
        for cat, patterns in custom_extension_rules.items():
            extension_rules.setdefault(cat, []).extend(patterns)

    # Normalize path for matching
    norm_path = path.replace("\\", "/").lower()

    # Pre-check: does filename match test or generated pattern?
    # This is used to skip source path boost for files that are clearly tests or generated
    is_test_by_filename = False
    is_generated_by_filename = False

    for pattern in filename_rules.get("test", []):
        try:
            if re.match(pattern, name, re.IGNORECASE):
                is_test_by_filename = True
                break
        except re.error:
            continue

    for pattern in filename_rules.get("generated", []):
        try:
            if re.match(pattern, name, re.IGNORECASE):
                is_generated_by_filename = True
                break
        except re.error:
            continue

    # Signal 1: Path rules
    # Sort categories to prioritize subcategories (more specific) over base categories
    # Subcategory patterns like "tests/unit/" should match before "tests/"
    sorted_categories = sorted(
        path_rules.keys(),
        key=lambda cat: ("::" not in cat, cat),  # Subcategories first, then alphabetical
    )

    matched_base_category = None
    for category in sorted_categories:
        patterns = path_rules[category]
        for pattern in patterns:
            pattern_lower = pattern.lower()
            # Source patterns should only match at path start to avoid conflicts
            # with paths like "vendor/github.com/pkg/" or "third_party/protobuf/src/"
            if category == "source":
                # Skip source path boost if file matches test or generated filename pattern
                # This ensures test files in src/ are still classified as tests, and
                # generated files like *.g.cs, *_pb2.py are still classified as generated
                if is_test_by_filename or is_generated_by_filename:
                    continue
                # Only match at the start of the path
                if not norm_path.startswith(pattern_lower):
                    continue
            else:
                # Other categories match at path segment boundaries
                # Require pattern at start of path OR preceded by /
                # This prevents "out/" from matching "About/" in paths like
                # "UI/ViewModels/About/"
                if not (norm_path.startswith(pattern_lower) or f"/{pattern_lower}" in f"/{norm_path}"):
                    continue

            # Pattern matched - apply scoring
            # If this is a subcategory, it takes precedence
            base_cat = category.split("::")[0] if "::" in category else category
            if "::" in category:
                # Subcategory match - clear any base category score and use this
                if base_cat in scores:
                    del scores[base_cat]
                scores[category] += w_path
                signals[f"path:{pattern}"] = category
                matched_base_category = base_cat
            elif base_cat != matched_base_category:
                # Base category - only score if no subcategory of this base matched
                scores[category] += w_path
                signals[f"path:{pattern}"] = category
            break  # Only count first matching pattern per category

    # Signal 2: Filename patterns
    for category, patterns in filename_rules.items():
        for pattern in patterns:
            try:
                if re.match(pattern, name, re.IGNORECASE):
                    scores[category] += w_filename
                    signals[f"filename:{pattern[:20]}..."] = category
                    break  # Only count first matching pattern per category
            except re.error:
                continue

    # Signal 3: Extension rules
    for category, extensions in extension_rules.items():
        if extension.lower() in [e.lower() for e in extensions]:
            scores[category] += w_extension
            signals[f"extension:{extension}"] = category

    # Default to source if no strong signals
    if not scores or max(scores.values()) < 0.4:
        scores["source"] = 0.3
        signals["default"] = "source"

    # Pick highest score
    best_category = max(scores, key=scores.get)
    raw_score = scores[best_category]

    # Normalize confidence to 0-1 range
    # Normalization factor based on max possible score
    max_weight = w_path + w_filename + w_extension
    norm_factor = max_weight / 1.5 if max_weight > 0 else 1.5
    confidence = min(raw_score / norm_factor, 1.0)

    # Build reason string from top signals
    reason_parts = [k for k, v in signals.items() if v == best_category]
    reason = ", ".join(reason_parts[:3])  # Top 3 reasons

    return ClassificationResult(
        category=best_category,
        confidence=round(confidence, 2),
        reason=reason,
        signals=signals
    )


def detect_language(
    name: str,
    extension: str,
    content: Optional[bytes] = None,
    validate: bool = False,
) -> LanguageResult:
    """
    Detect the programming language of a file.

    Uses go-enry for enhanced detection if available, with fallback to
    extension-based detection.

    Args:
        name: Filename
        extension: File extension including dot
        content: Optional file content for content-based detection (shebang, etc.)
        validate: If True and content provided, validate with tree-sitter parsing

    Returns:
        LanguageResult with language and confidence
    """
    # Display name → identifier mapping for languages with special characters
    DISPLAY_TO_IDENTIFIER = {
        "c#": "csharp",
        "c++": "cpp",
        "f#": "fsharp",
        "objective-c": "objective-c",
        "objective-c++": "objective-cpp",
    }

    # Try enhanced detection if available (includes shebang detection)
    if ENHANCED_DETECTION:
        try:
            result = _detect_language_enhanced(name, content, validate)
            if result.language != "unknown":
                lang_lower = result.language.lower()

                # First check if it's a display name that needs mapping
                if lang_lower in DISPLAY_TO_IDENTIFIER:
                    return LanguageResult(
                        language=DISPLAY_TO_IDENTIFIER[lang_lower],
                        confidence=result.confidence
                    )

                # Try to match with LANGUAGE_MAP for consistency
                for ext, mapped_lang in LANGUAGE_MAP.items():
                    if mapped_lang.lower() == lang_lower:
                        return LanguageResult(language=mapped_lang, confidence=result.confidence)

                # Return the detected language as-is (lowercase for consistency)
                return LanguageResult(language=lang_lower, confidence=result.confidence)
        except Exception:
            pass  # Fall through to basic detection

    # Fallback: Check exact filename first (for Makefile, Dockerfile, etc.)
    if name in LANGUAGE_MAP:
        return LanguageResult(language=LANGUAGE_MAP[name], confidence=1.0)

    # Check extension
    ext_lower = extension.lower()
    if ext_lower in LANGUAGE_MAP:
        return LanguageResult(language=LANGUAGE_MAP[ext_lower], confidence=0.95)

    # Unknown
    return LanguageResult(language="unknown", confidence=0.0)


# Directory name patterns that override content-based classification
# These well-known directory names have strong semantic meaning
DIRECTORY_NAME_RULES: Dict[str, List[str]] = {
    "source": ["src", "source", "lib", "pkg", "app", "internal", "cmd"],
    "test": ["test", "tests", "spec", "__tests__", "testing"],
    "docs": ["docs", "doc", "documentation"],
    "generated": ["build", "dist", "out", "target", "bin", "obj", "_build"],
    "vendor": ["vendor", "node_modules", "third_party"],
    "ci": [".github", ".gitlab-ci", ".circleci"],
}


def classify_directory(
    file_classifications: List[str],
) -> Tuple[str, str]:
    """
    Classify a directory based on its contents.

    Uses majority vote of child file classifications.

    Args:
        file_classifications: List of classifications from child files

    Returns:
        Tuple of (category, reason)
    """
    if not file_classifications:
        return "other", "empty directory"

    # Count classifications
    counts: Dict[str, int] = defaultdict(int)
    for cat in file_classifications:
        counts[cat] += 1

    # Find majority
    total = len(file_classifications)
    best_cat = max(counts, key=counts.get)
    best_count = counts[best_cat]
    percentage = (best_count / total) * 100

    return best_cat, f"majority {best_cat} ({percentage:.0f}%)"


def classify_directory_by_name(
    directory_name: str,
    file_classifications: List[str],
) -> Tuple[str, str]:
    """
    Classify directory using name heuristics first, then majority vote.

    Well-known directory names like 'src', 'tests', 'build' have strong
    semantic meaning that should override content-based classification.
    For example, a 'src' directory containing only generated files should
    still be classified as 'source' because its structural role is to
    contain source code.

    Args:
        directory_name: The name of the directory (not full path)
        file_classifications: List of classifications from child files

    Returns:
        Tuple of (category, reason)
    """
    dir_lower = directory_name.lower()

    # Check directory name heuristics first
    for category, names in DIRECTORY_NAME_RULES.items():
        if dir_lower in names:
            return category, f"directory_name:{directory_name}"

    # Fall back to majority vote
    return classify_directory(file_classifications)


def get_classification_distribution(
    file_classifications: List[str]
) -> Dict[str, int]:
    """Get distribution of classifications."""
    counts: Dict[str, int] = defaultdict(int)
    for cat in file_classifications:
        counts[cat] += 1
    return dict(counts)


def get_language_distribution(languages: List[str]) -> Dict[str, int]:
    """Get distribution of languages."""
    counts: Dict[str, int] = defaultdict(int)
    for lang in languages:
        if lang != "unknown":
            counts[lang] += 1
    return dict(counts)
