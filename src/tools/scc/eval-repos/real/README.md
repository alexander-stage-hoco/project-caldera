# Real Repositories for Evaluation

This directory contains git submodules pointing to small, well-known open source projects.
These provide real-world test cases for validating `scc` metrics against production codebases.

## Repositories

| Repository | Language | Size | Description |
|------------|----------|------|-------------|
| [envconfig](https://github.com/kelseyhightower/envconfig) | Go | Small (~1K LOC) | Environment variable configuration |
| [click](https://github.com/pallets/click) | Python | Medium (~15K LOC) | Command-line interface toolkit |
| [chalk](https://github.com/chalk/chalk) | JS/TS | Small (~500 LOC) | Terminal string styling |
| [Humanizer](https://github.com/Humanizr/Humanizer) | C# | Medium (~5K LOC) | String/date/number manipulation |
| [hashids.net](https://github.com/ullmark/hashids.net) | C# | Small (~1K LOC) | URL-safe ID encoding |
| [dayjs](https://github.com/iamkun/dayjs) | JS | Small (~3K LOC) | Lightweight date library |
| [nanoid](https://github.com/ai/nanoid) | JS | Tiny (~200 LOC) | Unique ID generator |
| [joda-money](https://github.com/JodaOrg/joda-money) | Java | Small (~3K LOC) | Money/currency handling |
| [picocli](https://github.com/remkop/picocli) | Java | Medium (~10K LOC) | CLI framework |

## Setup

After cloning the main repository, initialize and update submodules:

```bash
# Initialize and clone submodules
git submodule update --init --recursive

# Or if submodules already exist but need updating
git submodule update --recursive --remote
```

## Why These Repos?

### Go
- **envconfig** - Clean, idiomatic Go code with good test coverage. Small enough for quick validation.

### Python
- **click** - Well-maintained, production-quality Python. Moderate size with real-world complexity patterns.

### JavaScript/TypeScript
- **chalk** - Modern JS/TS patterns, minimal dependencies, modular structure.
- **dayjs** - Popular date library, well-tested with good documentation.
- **nanoid** - Minimal footprint, demonstrates concise JS patterns.

### C#
- **Humanizer** - Comprehensive utility library, good example of C# idioms.
- **hashids.net** - Small, focused library for ID encoding.

### Java
- **joda-money** - Clean, production-quality Java from the Joda project.
- **picocli** - Well-documented CLI framework with annotations.

## Expected Metrics Ranges

| Repository | LOC | Files | Avg CCN | Max CCN |
|------------|-----|-------|---------|---------|
| envconfig | 800-1,200 | 10-15 | 2-4 | 10-15 |
| click | 12,000-18,000 | 30-50 | 4-8 | 20-30 |
| chalk | 400-700 | 5-10 | 1-3 | 5-10 |
| Humanizer | 4,000-6,000 | 50-80 | 2-5 | 15-25 |
| hashids.net | 500-1,500 | 5-15 | 2-4 | 8-12 |
| dayjs | 2,000-4,000 | 30-50 | 2-4 | 10-15 |
| nanoid | 100-300 | 5-10 | 1-2 | 3-5 |
| joda-money | 2,000-4,000 | 20-40 | 2-4 | 10-15 |
| picocli | 8,000-12,000 | 30-60 | 3-6 | 20-30 |

*Note: Metrics may vary based on current version and development activity.*

## Updating Submodules

To pull latest changes from upstream:

```bash
cd eval-repos/real
git submodule foreach git pull origin main
```

Or update a specific submodule:

```bash
cd eval-repos/real/click
git pull origin main
```
