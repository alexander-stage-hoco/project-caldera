# PoC #10: License Inventory Analysis

Proof-of-concept for license detection and compliance analysis using pattern matching and SPDX detection.

## Quick Start

```bash
# Setup
make setup

# Build synthetic test repos
make build-repos

# Run analysis
make analyze

# Run evaluation
make evaluate

# Run LLM evaluation
make evaluate-llm
```

## What It Does

- Detects licenses in repositories via pattern matching
- Identifies SPDX headers in source code
- Classifies licenses by category (permissive, weak-copyleft, copyleft)
- Assesses overall license risk (low, medium, high, critical)

## Key Metrics

| Metric | Description |
|--------|-------------|
| `licenses_found` | List of detected SPDX license IDs |
| `license_counts` | Count per license type |
| `overall_risk` | Risk level: low, medium, high, critical |
| `has_copyleft` | True if GPL/AGPL detected (deal breaker) |
| `has_weak_copyleft` | True if LGPL/MPL detected |
| `license_files_found` | Count of LICENSE/COPYING files |
| `files_with_licenses` | Files with detected licenses |

## Risk Levels

| Risk | Category | Examples |
|------|----------|----------|
| `low` | Permissive only | MIT, Apache-2.0, BSD |
| `medium` | Weak copyleft | LGPL, MPL |
| `high` | No license found | All rights reserved |
| `critical` | Strong copyleft | GPL, AGPL |

## Test Repositories

| Repository | Licenses | Expected Risk |
|------------|----------|---------------|
| `mit-only` | MIT | low |
| `apache-bsd` | Apache-2.0, BSD-3-Clause | low |
| `gpl-mixed` | GPL-3.0-only | critical |
| `multi-license` | MIT, Apache-2.0, LGPL-2.1-only | medium |
| `no-license` | (none) | high |

## Evaluation Results

- **5 repositories tested**
- **28 checks per repository**
- **140/140 (100%) pass rate**

## License Categories

### Permissive (low risk)
- MIT
- Apache-2.0
- BSD-3-Clause
- BSD-2-Clause
- ISC

### Weak Copyleft (medium risk)
- LGPL-2.1-only
- LGPL-3.0-only
- MPL-2.0

### Strong Copyleft (critical risk)
- GPL-2.0-only
- GPL-3.0-only
- AGPL-3.0-only

## Output Schema

```json
{
  "schema_version": "1.0",
  "repository": "my-repo",
  "timestamp": "2025-01-06T12:00:00Z",
  "tool": "license-analyzer",
  "licenses_found": ["MIT", "Apache-2.0"],
  "license_counts": {"MIT": 5, "Apache-2.0": 3},
  "overall_risk": "low",
  "has_permissive": true,
  "has_copyleft": false,
  "has_weak_copyleft": false,
  "has_unknown": false,
  "findings": [
    {
      "file_path": "LICENSE",
      "spdx_id": "MIT",
      "category": "permissive",
      "confidence": 0.9,
      "match_type": "file"
    }
  ]
}
```

## Files

```
poc-scancode/
  scripts/
    license_analyzer.py      # Main analyzer
    create_synthetic_repos.py # Repo generator
    evaluate.py              # Evaluation runner
    checks/
      __init__.py           # Core types
      accuracy.py           # LA-1 to LA-10
      coverage.py           # LC-1 to LC-8
      detection.py          # LD-1 to LD-6
      performance.py        # LP-1 to LP-4
  eval-repos/synthetic/
    mit-only/
    gpl-mixed/
    apache-bsd/
    no-license/
    multi-license/
  evaluation/ground-truth/
    *.json                  # Ground truth files
  output/runs/
    *.json                  # Analysis results
```

## References

- [SPDX License List](https://spdx.org/licenses/)
- [Choose a License](https://choosealicense.com/)
- [Open Source Licenses Explained](https://opensource.org/licenses)
