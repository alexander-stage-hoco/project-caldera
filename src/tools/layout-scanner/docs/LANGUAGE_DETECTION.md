# Language Detection Module

Detailed documentation for the `language_detector.py` module in the Layout Scanner.

## Overview

The language detection module provides multi-strategy programming language identification for files. It uses a layered approach with optional enhanced detection via go-enry and robust built-in fallbacks.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    detect_language()                         │
│                    Main API Entry Point                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              detect_language_with_enry()                     │
│                                                              │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │  ENRY_AVAILABLE │───▶│ enry.get_language()          │   │
│  │     True        │    │ - Modeline detection         │   │
│  └─────────────────┘    │ - Filename matching          │   │
│          │              │ - Shebang parsing            │   │
│          │              │ - Extension matching         │   │
│          ▼              │ - Content heuristics         │   │
│  ┌─────────────────┐    │ - Bayesian classifier        │   │
│  │  ENRY_AVAILABLE │    └──────────────────────────────┘   │
│  │     False       │                                        │
│  └─────────────────┘                                        │
│          │                                                   │
│          ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          detect_language_by_extension()               │  │
│  │                                                        │  │
│  │  1. FILENAME_MAP (Makefile, Dockerfile, etc.)        │  │
│  │  2. EXTENSION_MAP (50+ extensions)                   │  │
│  │  3. detect_language_by_shebang() for scripts         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (optional)
┌─────────────────────────────────────────────────────────────┐
│              validate_with_treesitter()                      │
│              (if validate=True and content provided)        │
└─────────────────────────────────────────────────────────────┘
```

## Detection Strategies

### 1. go-enry (Primary - Optional)

When the `enry` package is available, it provides comprehensive detection using GitHub Linguist algorithms:

| Strategy | Description | Example |
|----------|-------------|---------|
| Modeline | vim/emacs markers | `# -*- mode: python -*-` |
| Filename | Known filenames | `Makefile` → Makefile |
| Shebang | Interpreter line | `#!/usr/bin/env python` |
| Extension | File extension | `.py` → Python |
| Content | Heuristics | Import patterns, syntax |
| Classifier | Bayesian | Statistical analysis |

**Installation Note**: go-enry requires a Go compiler to build from source. If unavailable, the module gracefully falls back to built-in detection.

### 2. Built-in Fallback

When enry is unavailable, the module uses a pure Python fallback:

#### Filename Detection
```python
FILENAME_MAP = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "CMakeLists.txt": "CMake",
    "Vagrantfile": "Ruby",
    "Gemfile": "Ruby",
    "Rakefile": "Ruby",
    # ... more mappings
}
```

#### Extension Detection
```python
EXTENSION_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".cs": "C#",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    # ... 50+ extensions
}
```

#### Shebang Detection

Parses the first line of files to detect interpreter:

```python
# Supported formats:
#!/usr/bin/env python          → Python
#!/bin/bash                    → Shell
#!/usr/bin/env python -u       → Python (with args)
#!/usr/bin/env -S python3 -u   → Python (env options)
```

**Interpreter Map:**
```python
SHEBANG_MAP = {
    "python": "Python",
    "python2": "Python",
    "python3": "Python",
    "ruby": "Ruby",
    "perl": "Perl",
    "bash": "Shell",
    "sh": "Shell",
    "zsh": "Shell",
    "node": "JavaScript",
    "php": "PHP",
    "lua": "Lua",
    # ... more interpreters
}
```

## Confidence Scoring

The module assigns confidence scores (0.0 to 1.0) based on detection certainty:

| Detection Method | Confidence | Reason |
|------------------|------------|--------|
| Unambiguous extension | 0.95 | `.py`, `.js`, `.rs` |
| Filename match | 0.90 | `Makefile`, `Dockerfile` |
| Shebang detection | 0.90 | Clear interpreter |
| enry with no alternatives | 0.95 | Unambiguous detection |
| enry with 1 alternative | 0.85 | Some ambiguity |
| enry with 2+ alternatives | 0.70 | Multiple possibilities |
| Ambiguous extension | 0.60 | `.h`, `.m` |
| Unknown | 0.00 | No match found |

### Ambiguous Extensions

Some extensions can represent multiple languages:

| Extension | Primary | Alternatives |
|-----------|---------|--------------|
| `.h` | C | C++, Objective-C |
| `.m` | Objective-C | MATLAB |
| `.pl` | Perl | Prolog |

## Special File Detection

### Binary File Detection

```python
is_binary_file(filename: str, content: Optional[bytes]) -> bool
```

Detects binary files using:
1. **Magic bytes** (header signatures):
   - PNG: `\x89PNG`
   - JPEG: `\xff\xd8\xff`
   - PDF: `%PDF`
   - ELF: `\x7fELF`
   - ZIP: `PK\x03\x04`
   - And more...

2. **Null byte detection**: Checks for `\x00` in first 8KB

### Vendor File Detection

```python
is_vendor_file(filename: str) -> bool
```

Detects vendor/dependency directories:
- `node_modules/`
- `vendor/`
- `third_party/`
- `external/`
- `bower_components/`
- `.nuget/`
- `packages/`

### Generated File Detection

```python
is_generated_file(filename: str, content: Optional[bytes]) -> bool
```

Detects auto-generated files by pattern:
- `.g.cs`, `.generated.*`
- `.min.js`, `.min.css`
- `.bundle.js`, `.d.ts`
- `_pb2.py`, `_pb2_grpc.py`, `.pb.go`
- `.designer.cs`
- `package-lock.json`, `yarn.lock`
- `pnpm-lock.yaml`, `poetry.lock`
- `go.sum`, `cargo.lock`

## API Reference

### Main Functions

#### `detect_language(filename, content=None, validate=False) -> LanguageResult`

Primary API for language detection.

**Parameters:**
- `filename`: File path or name
- `content`: Optional file content (bytes) for content-based detection
- `validate`: If True, validate with tree-sitter parsing

**Returns:** `LanguageResult` with:
- `language`: Detected language or "unknown"
- `confidence`: 0.0 to 1.0
- `method`: Detection method used
- `alternatives`: List of alternative candidates

**Example:**
```python
from scripts.language_detector import detect_language

# Extension-based
result = detect_language("main.py")
# LanguageResult(language='Python', confidence=0.95, method='extension', alternatives=[])

# Shebang-based
result = detect_language("script", b"#!/usr/bin/env python\nprint('hello')")
# LanguageResult(language='Python', confidence=0.9, method='shebang', alternatives=[])

# Ambiguous
result = detect_language("header.h")
# LanguageResult(language='C', confidence=0.6, method='extension', alternatives=['C', 'C++', 'Objective-C'])
```

#### `detect_language_by_shebang(content) -> Optional[str]`

Parse shebang line to detect language.

**Parameters:**
- `content`: File content as bytes

**Returns:** Language name or None

#### `detect_language_by_extension(filename, content=None) -> LanguageResult`

Extension and filename-based detection with optional shebang fallback.

### Utility Functions

#### `is_binary_file(filename, content=None) -> bool`
#### `is_vendor_file(filename) -> bool`
#### `is_generated_file(filename, content=None) -> bool`
#### `normalize_language(lang) -> str`
#### `get_detection_capabilities() -> dict`

Returns information about available detection strategies:
```python
{
    "enry_available": False,
    "treesitter_available": False,
    "strategies": ["filename", "extension", "shebang"],
    "fallback_only": True,
    "shebang_available": True
}
```

## Data Types

### LanguageResult

```python
@dataclass
class LanguageResult:
    language: str           # Detected language or "unknown"
    confidence: float       # 0.0 to 1.0
    method: str             # Detection method used
    alternatives: List[str] # Alternative language candidates
```

## Integration with Classifier

The language detector integrates with `classifier.py`:

```python
# classifier.py imports language detection
from .language_detector import (
    detect_language as _detect_language_enhanced,
    ENRY_AVAILABLE,
)

# detect_language() function uses enhanced detection when available
def detect_language(name: str, ext: str, content: Optional[bytes] = None) -> LanguageResult:
    if ENHANCED_DETECTION:
        result = _detect_language_enhanced(name, content)
        # Normalize display names to identifiers (C# → csharp)
        ...
    else:
        # Fallback to extension-only detection
        ...
```

## Testing

The module has comprehensive test coverage:

- **Unit tests**: `tests/unit/test_language_detector.py`
  - Shebang parsing (with args, env options, interpreters)
  - Extension detection (50+ extensions)
  - Binary file detection (magic bytes, null bytes)
  - Vendor/generated file detection

- **Integration tests**: `tests/integration/test_language_detection_integration.py`
  - Classifier ↔ language_detector interaction
  - Multi-language repository scenarios
  - Edge cases (uppercase extensions, dotfiles)

- **System tests**: `tests/system/test_language_detection_e2e.py`
  - Real-world repository structures (Flask, React, .NET)
  - Confidence scoring verification
  - Error recovery (corrupted content, encoding issues)

Run tests:
```bash
cd src/layout-scanner
python -m pytest tests/ -v -k "language"
```

## Performance

Language detection is fast:
- Extension lookup: O(1) hash table
- Shebang parsing: First line only
- Enry detection: Optimized C/Go implementation

No measurable impact on overall scan performance.
