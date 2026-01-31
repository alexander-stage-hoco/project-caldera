# Trivy Evaluation Scorecard

## Overview

| Metric | Value |
|--------|-------|
| **Tool** | trivy |
| **Last Evaluated** | 2026-01-29 |
| **Files Evaluated** | 15 |
| **Overall Pass Rate** | 93.3% |
| **Status** | Production Ready |

## Summary

| Category | Passed | Total | Pass Rate | Avg Score |
|----------|--------|-------|-----------|-----------|
| **Accuracy** | 30 | 30 | 100% | 1.0 |
| **Completeness** | 30 | 30 | 100% | 1.0 |
| **Coverage** | 10 | 15 | 66.7% | 0.67 |
| **Overall** | 70 | 75 | 93.3% | 0.93 |

## Programmatic Checks

| Check ID | Name | Status | Pass Rate |
|----------|------|--------|-----------|
| TR-AC-1 | Vulnerability count accuracy | PASS | 100% |
| TR-AC-2 | Critical count accuracy | PASS | 100% |
| TR-CM-3 | Metadata consistency | PASS | 100% |
| TR-CM-4 | Vulnerability required fields | PASS | 100% |
| TR-CV-1 | Target coverage | PARTIAL | 66.7% |

## Per-File Results

| File | Pass Rate | Status |
|------|-----------|--------|
| dotnet-outdated.json | 100% | PASS |
| js-fullstack.json | 100% | PASS |
| no-vulnerabilities.json | 100% | PASS |
| iac-misconfigs.json | 100% | PASS |
| mixed-severity.json | 100% | PASS |
| java-outdated.json | 100% | PASS |
| critical-cves.json | 100% | PASS |
| outdated-deps.json | 100% | PASS |
| cfn-misconfigs.json | 100% | PASS |
| k8s-misconfigs.json | 100% | PASS |
| .git.json | 80% | PARTIAL |
| .config.json | 80% | PARTIAL |
| .vscode.json | 80% | PARTIAL |
| .github.json | 80% | PARTIAL |
| csharp-complex.json | 80% | PARTIAL |

## LLM Judges

| Judge | Score | Confidence |
|-------|-------|------------|
| Vulnerability Accuracy | 4.0 | 0.8 |
| Coverage Completeness | 4.0 | 0.8 |
| Actionability | 4.0 | 0.8 |

**Combined LLM Score**: 4.0/5.0 (placeholder - implement actual LLM evaluation)

## Notes

- Target coverage check fails for hidden directory scans (`.git`, `.github`, etc.) which don't produce typical lockfile targets
- All core vulnerability scanning scenarios pass 100%
- Legacy format outputs are evaluated with lenient metadata checks
- Envelope format outputs are evaluated with strict metadata validation

## Recommendations

1. **Improve target coverage check** - Handle edge cases for non-package scans
2. **Implement LLM judges** - Replace placeholder scores with actual LLM evaluation
3. **Add more synthetic repos** - Cover additional package managers (Go, Ruby, Rust)
4. **Tighten ground truth ranges** - Current ranges are overly permissive

## Next Steps

- [ ] Run `make evaluate-llm` to generate actual LLM scores
- [ ] Add ground truth for missing repositories
- [ ] Implement additional programmatic checks (TR-AC-3 to TR-AC-5, TR-CV-2, TR-CV-3)
