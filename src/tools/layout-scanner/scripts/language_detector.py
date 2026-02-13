"""
Language Detection Module for Layout Scanner.

Multi-strategy language detection using go-enry with fallback to extension-based detection.

Detection strategies (in order of priority):
1. Enry primary detection (filename + content)
   - Modeline detection (vim/emacs markers)
   - Filename matching
   - Shebang parsing
   - Extension matching
   - Content heuristics
   - Bayesian classifier
2. Fallback: Extension-based detection (if enry unavailable)

Optionally validates language detection using tree-sitter parsing.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Try to import enry (optional - has build requirements)
try:
    import enry
    ENRY_AVAILABLE = True
except ImportError:
    ENRY_AVAILABLE = False

# Shebang interpreter to language mapping
SHEBANG_MAP = {
    "python": "Python",
    "python2": "Python",
    "python3": "Python",
    "ruby": "Ruby",
    "perl": "Perl",
    "bash": "Shell",
    "sh": "Shell",
    "zsh": "Shell",
    "fish": "Shell",
    "node": "JavaScript",
    "nodejs": "JavaScript",
    "php": "PHP",
    "lua": "Lua",
    "groovy": "Groovy",
    "awk": "AWK",
    "sed": "Shell",
    "tclsh": "Tcl",
    "wish": "Tcl",
    "elixir": "Elixir",
    "escript": "Erlang",
    "runhaskell": "Haskell",
    "osascript": "AppleScript",
    "Rscript": "R",
}

# Try to import tree-sitter for validation (optional)
try:
    from tree_sitter_language_pack import get_language, get_parser
    TREESITTER_AVAILABLE = True
except ImportError:
    TREESITTER_AVAILABLE = False


@dataclass
class LanguageResult:
    """Result of language detection."""
    language: str           # Detected language or "unknown"
    confidence: float       # 0.0 to 1.0
    method: str             # Detection method used
    alternatives: list[str] # Alternative language candidates


# Extension-based language mapping (fallback)
EXTENSION_MAP = {
    # Python
    ".py": "Python",
    ".pyw": "Python",
    ".pyi": "Python",
    ".pyx": "Python",
    # JavaScript/TypeScript
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    # C#
    ".cs": "C#",
    ".csx": "C#",
    # Java/Kotlin
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    # Go
    ".go": "Go",
    # Rust
    ".rs": "Rust",
    # C/C++
    ".c": "C",
    ".h": "C",  # Ambiguous - could be C, C++, or Objective-C
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".hh": "C++",
    ".hxx": "C++",
    # Ruby
    ".rb": "Ruby",
    ".rake": "Ruby",
    ".gemspec": "Ruby",
    # PHP
    ".php": "PHP",
    ".phtml": "PHP",
    # Swift
    ".swift": "Swift",
    # Objective-C
    ".m": "Objective-C",
    ".mm": "Objective-C",
    # Shell
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    # PowerShell
    ".ps1": "PowerShell",
    ".psm1": "PowerShell",
    ".psd1": "PowerShell",
    # Scala
    ".scala": "Scala",
    ".sc": "Scala",
    # Elixir
    ".ex": "Elixir",
    ".exs": "Elixir",
    # Clojure
    ".clj": "Clojure",
    ".cljs": "ClojureScript",
    ".cljc": "Clojure",
    # Haskell
    ".hs": "Haskell",
    ".lhs": "Haskell",
    # Lua
    ".lua": "Lua",
    # Perl
    ".pl": "Perl",
    ".pm": "Perl",
    # R
    ".r": "R",
    ".R": "R",
    # SQL
    ".sql": "SQL",
    # YAML
    ".yaml": "YAML",
    ".yml": "YAML",
    # JSON
    ".json": "JSON",
    ".jsonc": "JSON",
    ".json5": "JSON",
    # XML
    ".xml": "XML",
    ".xsl": "XML",
    ".xslt": "XML",
    ".xsd": "XML",
    ".xaml": "XAML",  # WPF/UWP/Avalonia markup
    # MSBuild project files
    ".csproj": "MSBuild",
    ".fsproj": "MSBuild",
    ".vbproj": "MSBuild",
    ".vcxproj": "MSBuild",
    ".vcproj": "MSBuild",
    ".proj": "MSBuild",
    ".targets": "MSBuild",
    ".props": "MSBuild",
    # .NET resource files (part of MSBuild system)
    ".resx": "MSBuild",
    # NDepend project files
    ".ndproj": "XML",
    # NuGet package specification
    ".nuspec": "nuspec",
    # HTML
    ".html": "HTML",
    ".htm": "HTML",
    # CSS
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    # Markdown
    ".md": "Markdown",
    ".markdown": "Markdown",
    # TOML
    ".toml": "TOML",
    # INI
    ".ini": "INI",
    ".cfg": "INI",
    ".conf": "INI",
    # HCL (Terraform, Packer, etc.)
    ".tf": "HCL",
    ".tfvars": "HCL",
    ".hcl": "HCL",
    # Solution files
    ".sln": "sln",
    # .NET config files
    ".config": "XML",
}

# Filename-based language mapping
FILENAME_MAP = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "CMakeLists.txt": "CMake",
    "Vagrantfile": "Ruby",
    "Gemfile": "Ruby",
    "Rakefile": "Ruby",
    "Brewfile": "Ruby",
    "Podfile": "Ruby",
    "Fastfile": "Ruby",
    ".gitignore": "gitignore",
    ".gitattributes": "gitattributes",
    ".editorconfig": "editorconfig",
    ".prettierrc": "JSON",
    ".eslintrc": "JSON",
    ".babelrc": "JSON",
    # Go module files
    "go.mod": "Go",
    "go.sum": "Go",
    # Python dependency files
    "requirements.txt": "pip",
    # License files
    "LICENSE": "license",
    "LICENSE.txt": "license",
    "COPYING": "license",
}

# Enry language name normalization (enry uses different casing/naming)
ENRY_LANGUAGE_MAP = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "c#": "C#",
    "c++": "C++",
    "c": "C",
    "go": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "java": "Java",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "swift": "Swift",
    "objective-c": "Objective-C",
    "shell": "Shell",
    "bash": "Shell",
    "powershell": "PowerShell",
    "php": "PHP",
    "html": "HTML",
    "css": "CSS",
    "scss": "SCSS",
    "less": "Less",
    "sql": "SQL",
    "json": "JSON",
    "yaml": "YAML",
    "xml": "XML",
    "markdown": "Markdown",
    "dockerfile": "Dockerfile",
    "makefile": "Makefile",
}

# Tree-sitter language name mapping (tree-sitter uses lowercase)
TREESITTER_LANGUAGE_MAP = {
    "Python": "python",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "C#": "csharp",
    "C++": "cpp",
    "C": "c",
    "Go": "go",
    "Rust": "rust",
    "Ruby": "ruby",
    "Java": "java",
    "Kotlin": "kotlin",
    "Scala": "scala",
    "Swift": "swift",
    "PHP": "php",
    "HTML": "html",
    "CSS": "css",
    "JSON": "json",
    "YAML": "yaml",
    "Markdown": "markdown",
}


def normalize_language(lang: str) -> str:
    """Normalize language name to consistent casing."""
    if not lang:
        return "unknown"
    return ENRY_LANGUAGE_MAP.get(lang.lower(), lang)


def detect_language_by_shebang(content: bytes) -> str | None:
    """
    Detect language from shebang line in file content.

    Args:
        content: File content as bytes

    Returns:
        Language name if detected, None otherwise
    """
    if not content:
        return None

    # Get first line
    try:
        first_line = content.split(b'\n', 1)[0].decode('utf-8', errors='ignore').strip()
    except Exception:
        return None

    # Check for shebang
    if not first_line.startswith('#!'):
        return None

    shebang = first_line[2:].strip()

    # Handle "#!/usr/bin/env interpreter [args]" format
    if '/env ' in shebang or shebang.startswith('env '):
        parts = shebang.split()
        # Find the interpreter (first part after 'env' that doesn't start with '-')
        interpreter = None
        found_env = False
        for part in parts:
            if part.endswith('env') or part == 'env':
                found_env = True
                continue
            if found_env:
                # Skip env options (e.g., -S, -i)
                if part.startswith('-'):
                    continue
                interpreter = part
                break
        if not interpreter:
            return None
    else:
        # Handle "#!/path/to/interpreter" format
        interpreter = shebang.split('/')[-1]
        # Remove any arguments (e.g., "python -u")
        interpreter = interpreter.split()[0] if interpreter else None

    if not interpreter:
        return None

    # Look up interpreter in map
    return SHEBANG_MAP.get(interpreter)


def detect_language_by_extension(filename: str, content: bytes | None = None) -> LanguageResult:
    """Detect language using extension-based mapping with optional shebang detection.

    Args:
        filename: Filename or path to detect language for
        content: Optional file content for shebang-based detection

    Returns:
        LanguageResult with language, confidence, method, and alternatives
    """
    path = Path(filename)
    name = path.name
    ext = path.suffix.lower()

    # Check filename first
    if name in FILENAME_MAP:
        return LanguageResult(
            language=FILENAME_MAP[name],
            confidence=0.9,
            method="filename",
            alternatives=[]
        )

    # Check extension
    if ext in EXTENSION_MAP:
        # Some extensions are ambiguous
        ambiguous = {".h": ["C", "C++", "Objective-C"], ".m": ["Objective-C", "MATLAB"]}
        if ext in ambiguous:
            return LanguageResult(
                language=EXTENSION_MAP[ext],
                confidence=0.6,
                method="extension",
                alternatives=ambiguous[ext]
            )
        return LanguageResult(
            language=EXTENSION_MAP[ext],
            confidence=0.95,
            method="extension",
            alternatives=[]
        )

    # Try shebang detection if content provided and no extension match
    if content:
        shebang_lang = detect_language_by_shebang(content)
        if shebang_lang:
            return LanguageResult(
                language=shebang_lang,
                confidence=0.9,
                method="shebang",
                alternatives=[]
            )

    return LanguageResult(
        language="unknown",
        confidence=0.0,
        method="none",
        alternatives=[]
    )


def detect_language_with_enry(filename: str, content: bytes | None = None) -> LanguageResult:
    """Detect language using go-enry (primary method) or fallback to enhanced extension detection."""
    if not ENRY_AVAILABLE:
        return detect_language_by_extension(filename, content)

    try:
        # Use enry for detection
        if content:
            # Full detection with content
            lang = enry.get_language(filename, content)
            alternatives_raw = enry.get_languages(filename, content)
        else:
            # Filename-only detection
            lang = enry.get_language(filename, b"")
            alternatives_raw = enry.get_languages(filename, b"")

        # Normalize language name
        language = normalize_language(lang) if lang else "unknown"

        # Get alternatives (excluding primary)
        alternatives = [normalize_language(a) for a in (alternatives_raw or []) if a and a != lang]

        # Determine confidence based on alternatives
        if not lang:
            confidence = 0.0
        elif not alternatives:
            confidence = 0.95  # High confidence when unambiguous
        elif len(alternatives) == 1:
            confidence = 0.85  # Good confidence with one alternative
        else:
            confidence = 0.7   # Lower confidence with multiple alternatives

        return LanguageResult(
            language=language,
            confidence=confidence,
            method="enry",
            alternatives=alternatives
        )

    except Exception as e:
        # Fall back to extension-based detection on error
        result = detect_language_by_extension(filename)
        result.method = f"extension (enry error: {e})"
        return result


def validate_with_treesitter(language: str, content: bytes) -> float:
    """
    Validate language detection by attempting to parse with tree-sitter.

    Returns a confidence modifier:
    - 1.0: Parse succeeded with no errors
    - 0.9: Parse succeeded with minor errors (<5)
    - 0.7: Parse succeeded with many errors
    - 0.5: Parse failed completely
    - 1.0: Parser not available (don't modify confidence)
    """
    if not TREESITTER_AVAILABLE:
        return 1.0  # No validation available

    ts_lang = TREESITTER_LANGUAGE_MAP.get(language)
    if not ts_lang:
        return 1.0  # No tree-sitter grammar for this language

    try:
        parser = get_parser(ts_lang)
        tree = parser.parse(content)

        # Count parse errors
        error_count = count_parse_errors(tree.root_node)

        if error_count == 0:
            return 1.0   # Perfect parse
        elif error_count < 5:
            return 0.9   # Minor issues
        elif error_count < 20:
            return 0.7   # Moderate issues
        else:
            return 0.5   # Major issues - likely wrong language

    except Exception:
        return 1.0  # Parser error, don't modify confidence


def count_parse_errors(node) -> int:
    """Count ERROR and MISSING nodes in a tree-sitter parse tree."""
    count = 0
    if node.type == "ERROR" or node.is_missing:
        count = 1
    for child in node.children:
        count += count_parse_errors(child)
    return count


def detect_language(
    filename: str,
    content: bytes | None = None,
    validate: bool = False
) -> LanguageResult:
    """
    Detect the programming language of a file.

    This is the main API function that combines all detection strategies.

    Args:
        filename: Filename or path to detect language for
        content: Optional file content for content-based detection
        validate: If True, validate detection with tree-sitter parsing

    Returns:
        LanguageResult with language, confidence, method, and alternatives

    Example:
        >>> detect_language("script", b"#!/usr/bin/env python\\nprint('hello')")
        LanguageResult(language='Python', confidence=0.95, method='enry', alternatives=[])

        >>> detect_language("header.h", b"#import <Foundation/Foundation.h>")
        LanguageResult(language='Objective-C', confidence=0.85, method='enry', alternatives=['C', 'C++'])
    """
    # Primary detection using enry (or fallback to extension)
    result = detect_language_with_enry(filename, content)

    # Optional tree-sitter validation
    if validate and content and result.language != "unknown":
        confidence_modifier = validate_with_treesitter(result.language, content)
        result.confidence *= confidence_modifier
        if confidence_modifier < 1.0:
            result.method += f" (validated: {confidence_modifier:.1f})"

    return result


def is_binary_file(filename: str, content: bytes | None = None) -> bool:
    """Check if a file is binary (not text)."""
    if ENRY_AVAILABLE and content:
        try:
            return enry.is_binary(content)
        except Exception:
            pass

    # Fallback: check for magic bytes or null bytes
    if content:
        # Check for common binary file magic bytes
        binary_magic = [
            b'\x89PNG',           # PNG image
            b'\xff\xd8\xff',      # JPEG image
            b'GIF87a', b'GIF89a', # GIF image
            b'PK\x03\x04',        # ZIP archive
            b'\x1f\x8b',          # gzip
            b'BZh',               # bzip2
            b'\x7fELF',           # ELF executable
            b'MZ',                # DOS/PE executable
            b'\xca\xfe\xba\xbe',  # Mach-O fat binary
            b'\xfe\xed\xfa\xce',  # Mach-O 32-bit
            b'\xfe\xed\xfa\xcf',  # Mach-O 64-bit
            b'\xcf\xfa\xed\xfe',  # Mach-O 64-bit (reversed)
            b'%PDF',              # PDF document
        ]
        for magic in binary_magic:
            if content.startswith(magic):
                return True

        # Check for null bytes in first 8KB
        sample = content[:8192]
        return b'\x00' in sample

    return False


def is_vendor_file(filename: str) -> bool:
    """Check if a file is in a vendor/dependencies directory."""
    if ENRY_AVAILABLE:
        try:
            return enry.is_vendor(filename)
        except Exception:
            pass

    # Fallback: simple path check
    vendor_patterns = [
        "vendor/", "node_modules/", "third_party/", "external/",
        "bower_components/", "jspm_packages/", ".nuget/", "packages/"
    ]
    filename_lower = filename.lower().replace("\\", "/")
    return any(p in filename_lower for p in vendor_patterns)


def is_generated_file(filename: str, content: bytes | None = None) -> bool:
    """Check if a file is auto-generated."""
    if ENRY_AVAILABLE and content:
        try:
            return enry.is_generated(filename, content)
        except Exception:
            pass

    # Fallback: pattern check
    name_lower = filename.lower()
    generated_patterns = [
        ".g.cs", ".generated.", ".min.js", ".min.css",
        ".bundle.js", ".d.ts", "_pb2.py", "_pb2_grpc.py", ".pb.go",
        ".designer.cs", "package-lock.json", "yarn.lock",
        "pnpm-lock.yaml", "pipfile.lock", "poetry.lock",
        "go.sum", "cargo.lock"
    ]
    return any(p in name_lower for p in generated_patterns)


def get_detection_capabilities() -> dict:
    """Get information about available detection capabilities."""
    strategies = [
        "filename",
        "extension",
        "shebang",  # Always available (built-in)
    ]

    if ENRY_AVAILABLE:
        strategies.extend(["modeline", "content", "classifier"])
    if TREESITTER_AVAILABLE:
        strategies.append("treesitter_validation")

    return {
        "enry_available": ENRY_AVAILABLE,
        "treesitter_available": TREESITTER_AVAILABLE,
        "strategies": strategies,
        "fallback_only": not ENRY_AVAILABLE,
        "shebang_available": True,  # Always available with built-in detection
    }


# Convenience exports
__all__ = [
    "LanguageResult",
    "detect_language",
    "detect_language_by_extension",
    "detect_language_by_shebang",
    "detect_language_with_enry",
    "validate_with_treesitter",
    "is_binary_file",
    "is_vendor_file",
    "is_generated_file",
    "get_detection_capabilities",
    "ENRY_AVAILABLE",
    "TREESITTER_AVAILABLE",
]
