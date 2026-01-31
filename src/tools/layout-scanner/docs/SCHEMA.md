# Layout Scanner Output Schema

This document describes the JSON output format produced by the Layout Scanner.

## Schema Version

Current schema version: `1.0`

The schema is defined in `schemas/layout.json` and can be used to validate output.

## Root Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | Yes | Always "1.0" |
| `tool` | string | Yes | Always "layout-scanner" |
| `tool_version` | string | Yes | Semantic version (e.g., "1.0.0") |
| `run_id` | string | Yes | Unique run identifier: `layout-YYYYMMDD-HHMMSS-{hash}` |
| `timestamp` | string | Yes | ISO 8601 timestamp of scan start |
| `repository` | string | Yes | Repository name (directory basename) |
| `repository_path` | string | Yes | Absolute path to scanned repository |
| `passes_completed` | array | Yes | List of completed passes: "filesystem", "git", "content" |
| `statistics` | object | Yes | Aggregate statistics |
| `files` | object | Yes | Map of relative path to file object |
| `directories` | object | Yes | Map of relative path to directory object |
| `hierarchy` | object | Yes | Tree structure information |

## Statistics Object

| Field | Type | Description |
|-------|------|-------------|
| `total_files` | integer | Total number of files scanned |
| `total_directories` | integer | Total number of directories |
| `total_size_bytes` | integer | Sum of all file sizes |
| `max_depth` | integer | Maximum directory nesting depth |
| `scan_duration_ms` | integer | Scan time in milliseconds |
| `files_per_second` | number | Processing throughput |
| `by_classification` | object | File count per classification category |
| `by_language` | object | File count per detected language |

## File Object

Each file entry in the `files` map has these fields:

### Core Fields (Always Present)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique file ID: `f-{12 hex chars}` |
| `path` | string | Relative path from repository root |
| `name` | string | Filename (basename) |
| `extension` | string | File extension including dot (e.g., ".py") |
| `size_bytes` | integer | File size in bytes |
| `modified_time` | string | Last modification time (ISO 8601) |
| `is_symlink` | boolean | Whether file is a symbolic link |
| `language` | string | Detected programming language or "unknown" |
| `classification` | string | File category (see Classification) |
| `classification_reason` | string | Human-readable explanation |
| `classification_confidence` | number | Confidence score 0.0-1.0 |
| `parent_directory_id` | string | Parent directory ID |
| `depth` | integer | Depth in directory tree (0 = root level) |

### Git Metadata Fields (Optional, requires `--git`)

| Field | Type | Description |
|-------|------|-------------|
| `first_commit_date` | string/null | Date of first commit touching this file |
| `last_commit_date` | string/null | Date of most recent commit |
| `commit_count` | integer/null | Number of commits touching this file |
| `author_count` | integer/null | Number of unique authors |

### Content Metadata Fields (Optional, requires `--content`)

| Field | Type | Description |
|-------|------|-------------|
| `content_hash` | string/null | SHA-256 hash of file contents |
| `is_binary` | boolean/null | Whether file is binary |
| `line_count` | integer/null | Number of lines (text files only) |

## Directory Object

Each directory entry in the `directories` map has these fields:

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique directory ID: `d-{12 hex chars}` |
| `path` | string | Relative path from repository root |
| `name` | string | Directory name (basename) |
| `modified_time` | string | Last modification time (ISO 8601) |
| `is_symlink` | boolean | Whether directory is a symbolic link |
| `classification` | string | Directory category based on contents |
| `classification_reason` | string | Human-readable explanation |
| `parent_directory_id` | string/null | Parent directory ID (null for root) |
| `depth` | integer | Depth in directory tree |

### Child References

| Field | Type | Description |
|-------|------|-------------|
| `child_directory_ids` | array | IDs of immediate child directories |
| `child_file_ids` | array | IDs of immediate child files |

### Metrics

| Field | Type | Description |
|-------|------|-------------|
| `direct_file_count` | integer | Files directly in this directory |
| `direct_directory_count` | integer | Subdirectories directly in this directory |
| `recursive_file_count` | integer | Total files in entire subtree |
| `recursive_directory_count` | integer | Total directories in entire subtree |
| `direct_size_bytes` | integer | Size of files directly in directory |
| `recursive_size_bytes` | integer | Total size of entire subtree |
| `classification_distribution` | object | File count by classification in subtree |
| `language_distribution` | object | File count by language in subtree |

## Hierarchy Object

| Field | Type | Description |
|-------|------|-------------|
| `root_id` | string | ID of the root directory |
| `max_depth` | integer | Maximum directory depth |
| `total_files` | integer | Total file count |
| `total_directories` | integer | Total directory count |
| `total_size_bytes` | integer | Total size |
| `children` | object | Map of parent ID to array of child IDs |
| `parents` | object | Map of child ID to parent ID |
| `depth_distribution` | object | Count of items at each depth level |

## Classification Categories

Files and directories are classified into these categories:

| Category | Description |
|----------|-------------|
| `source` | Production source code |
| `test` | Test files and fixtures |
| `config` | Configuration files |
| `generated` | Auto-generated code |
| `docs` | Documentation |
| `vendor` | Third-party dependencies |
| `build` | Build artifacts |
| `ci` | CI/CD configuration |
| `other` | Unclassified |

### Subcategories

Classifications can include subcategories using `::` syntax:

- `test::unit` - Unit tests
- `test::integration` - Integration tests
- `test::e2e` - End-to-end tests
- `config::build` - Build configuration
- `config::lint` - Linter configuration
- `config::ci` - CI configuration

## ID Format

IDs are stable content-based identifiers:

- **File IDs**: `f-{12 hex chars}` (e.g., `f-a1b2c3d4e5f6`)
- **Directory IDs**: `d-{12 hex chars}` (e.g., `d-1a2b3c4d5e6f`)

IDs are generated from the relative path using SHA-256 hashing, ensuring consistency across runs for the same repository structure.

## Example Output

```json
{
  "schema_version": "1.0",
  "tool": "layout-scanner",
  "tool_version": "1.0.0",
  "run_id": "layout-20260110-143052-abc123",
  "timestamp": "2026-01-10T14:30:52Z",
  "repository": "my-project",
  "repository_path": "/home/user/my-project",
  "passes_completed": ["filesystem"],
  "statistics": {
    "total_files": 150,
    "total_directories": 25,
    "total_size_bytes": 524288,
    "max_depth": 5,
    "scan_duration_ms": 45,
    "files_per_second": 3333.33,
    "by_classification": {
      "source": 100,
      "test": 30,
      "config": 15,
      "docs": 5
    },
    "by_language": {
      "python": 80,
      "javascript": 40,
      "yaml": 15,
      "markdown": 5,
      "unknown": 10
    }
  },
  "files": {
    "src/main.py": {
      "id": "f-a1b2c3d4e5f6",
      "path": "src/main.py",
      "name": "main.py",
      "extension": ".py",
      "size_bytes": 2048,
      "modified_time": "2026-01-09T10:30:00Z",
      "is_symlink": false,
      "language": "python",
      "classification": "source",
      "classification_reason": "default",
      "classification_confidence": 0.3,
      "parent_directory_id": "d-1a2b3c4d5e6f",
      "depth": 1
    },
    "tests/unit/test_main.py": {
      "id": "f-b2c3d4e5f6a7",
      "path": "tests/unit/test_main.py",
      "name": "test_main.py",
      "extension": ".py",
      "size_bytes": 1024,
      "modified_time": "2026-01-08T15:00:00Z",
      "is_symlink": false,
      "language": "python",
      "classification": "test::unit",
      "classification_reason": "path:tests/unit/",
      "classification_confidence": 0.6,
      "parent_directory_id": "d-2b3c4d5e6f7a",
      "depth": 2
    }
  },
  "directories": {
    ".": {
      "id": "d-000000000000",
      "path": ".",
      "name": "my-project",
      "modified_time": "2026-01-10T14:30:00Z",
      "is_symlink": false,
      "classification": "source",
      "classification_reason": "majority (67%)",
      "parent_directory_id": null,
      "depth": 0,
      "child_directory_ids": ["d-1a2b3c4d5e6f", "d-3c4d5e6f7a8b"],
      "child_file_ids": ["f-c3d4e5f6a7b8"],
      "direct_file_count": 1,
      "direct_directory_count": 2,
      "recursive_file_count": 150,
      "recursive_directory_count": 25,
      "direct_size_bytes": 512,
      "recursive_size_bytes": 524288,
      "classification_distribution": {
        "source": 100,
        "test": 30,
        "config": 15,
        "docs": 5
      },
      "language_distribution": {
        "python": 80,
        "javascript": 40
      }
    }
  },
  "hierarchy": {
    "root_id": "d-000000000000",
    "max_depth": 5,
    "total_files": 150,
    "total_directories": 25,
    "total_size_bytes": 524288,
    "children": {
      "d-000000000000": ["d-1a2b3c4d5e6f", "d-3c4d5e6f7a8b", "f-c3d4e5f6a7b8"]
    },
    "parents": {
      "d-1a2b3c4d5e6f": "d-000000000000",
      "f-c3d4e5f6a7b8": "d-000000000000"
    },
    "depth_distribution": {
      "0": 1,
      "1": 10,
      "2": 50,
      "3": 80,
      "4": 30,
      "5": 5
    }
  }
}
```

## Validation

To validate output against the schema:

```bash
# Using the built-in validator
python -m scripts.schema_validator output.json

# With specific validation levels
python -m scripts.schema_validator output.json --level all

# Output as JSON
python -m scripts.schema_validator output.json --json
```

Validation levels:
- `schema` - JSON structure and types
- `referential` - ID references are valid
- `consistency` - Statistics match actual counts
- `all` - All levels (default)
