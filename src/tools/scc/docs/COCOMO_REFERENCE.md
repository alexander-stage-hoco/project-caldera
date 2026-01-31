# COCOMO Cost Estimation Reference

## Overview

COCOMO (Constructive Cost Model) is an algorithmic software cost estimation model that uses lines of code (LOC) to estimate development effort, schedule, and cost.

## The COCOMO Formula

```
Effort (person-months) = a × (KLOC)^b × EAF
Schedule (months) = c × (Effort)^d
Cost = Effort × (avg_wage / 12) × overhead
People = Effort / Schedule
```

Where:
- **KLOC** = Thousands of Lines of Code
- **a, b** = Effort coefficients (project type dependent)
- **c, d** = Schedule coefficients
- **EAF** = Effort Adjustment Factor (project-specific)

---

## Parameter Definitions

| Parameter | Name | Description | Typical Range |
|-----------|------|-------------|---------------|
| `a` | Effort Multiplier | Base effort factor that scales with project complexity | 2.0 - 4.0 |
| `b` | Effort Exponent | Non-linear scaling of effort with size (diseconomy of scale) | 1.0 - 1.25 |
| `c` | Schedule Multiplier | Base schedule factor | 2.0 - 3.0 |
| `d` | Schedule Exponent | Schedule compression factor (higher = less compression) | 0.30 - 0.42 |
| `avg_wage` | Average Annual Salary | Fully-loaded developer cost (salary + benefits + taxes) | $60K - $250K |
| `overhead` | Overhead Factor | Non-development costs (tools, infrastructure, management) | 1.5 - 3.5 |
| `eaf` | Effort Adjustment Factor | Project-specific multiplier for complexity/risk | 0.5 - 2.0 |

### Parameter Effects

| If you increase... | Effect on... |
|-------------------|--------------|
| `a` (effort multiplier) | More person-months for same LOC |
| `b` (effort exponent) | Larger projects become disproportionately more expensive |
| `c` (schedule multiplier) | Longer schedules |
| `d` (schedule exponent) | Less schedule compression possible |
| `avg_wage` | Higher cost (linear) |
| `overhead` | Higher cost (linear) |
| `eaf` | More effort required (risk/complexity adjustment) |

---

## Standard COCOMO Project Types

| Type | a | b | c | d | Description |
|------|---|---|---|---|-------------|
| **Organic** | 2.4 | 1.05 | 2.5 | 0.38 | Small teams, familiar tech, relaxed requirements |
| **Semi-Detached** | 3.0 | 1.12 | 2.5 | 0.35 | Medium teams, mixed experience, some constraints |
| **Embedded** | 3.6 | 1.20 | 2.5 | 0.32 | High reliability, tight constraints, complex interfaces |

---

## Organization-Specific Presets

Based on typical organizational characteristics, we define the following presets:

### Coefficient Table

| Organization Type | a | b | c | d | avg_wage | overhead | eaf | Typical Use Case |
|-------------------|---|---|---|---|----------|----------|-----|------------------|
| **early_startup** | 2.0 | 1.00 | 2.2 | 0.40 | $150,000 | 1.5 | 0.8 | < 10 employees, flat structure, no bureaucracy |
| **growth_startup** | 2.4 | 1.05 | 2.5 | 0.38 | $140,000 | 1.8 | 0.9 | 10-50 employees, adding process |
| **scale_up** | 2.8 | 1.08 | 2.5 | 0.36 | $130,000 | 2.2 | 1.0 | 50-200 employees, formal processes emerging |
| **sme** | 3.0 | 1.12 | 2.5 | 0.35 | $120,000 | 2.4 | 1.0 | 200-500 employees, established processes |
| **mid_market** | 3.2 | 1.15 | 2.5 | 0.34 | $115,000 | 2.6 | 1.1 | 500-2000 employees, compliance overhead |
| **large_enterprise** | 3.6 | 1.20 | 2.5 | 0.32 | $110,000 | 3.0 | 1.2 | 2000+ employees, heavy governance |
| **regulated** | 4.0 | 1.25 | 2.8 | 0.30 | $120,000 | 3.5 | 1.5 | Finance, Healthcare, Defense, Government |
| **open_source** | 2.0 | 1.00 | 3.0 | 0.42 | $0 | 1.0 | 0.5 | Volunteer, no cost model applicable |

### Preset Rationale

**Early Startup (a=2.0, b=1.00)**
- Linear scaling (b=1.0) because small codebase, no coordination overhead
- Low overhead (1.5x) - minimal non-development costs
- High wages ($150K) - competitive to attract talent
- Low EAF (0.8) - move fast, break things

**SME (a=3.0, b=1.12)**
- Standard semi-detached model
- Moderate overhead (2.4x) - established infrastructure
- Normal EAF (1.0) - balanced risk/quality

**Large Enterprise (a=3.6, b=1.20)**
- Embedded model - complex systems, many dependencies
- High overhead (3.0x) - significant governance, security, compliance
- Higher EAF (1.2) - quality gates, change control

**Regulated Industry (a=4.0, b=1.25)**
- Highest coefficients - extensive documentation, auditing
- Very high overhead (3.5x) - compliance, security, audit trails
- Highest EAF (1.5) - rigorous testing, validation

---

## Example Calculations

### 10,000 LOC Codebase

| Organization | Effort (PM) | Schedule (mo) | People | Cost |
|--------------|-------------|---------------|--------|------|
| Early Startup | 16.0 | 7.5 | 2.1 | $300K |
| Growth Startup | 22.4 | 8.4 | 2.7 | $504K |
| Scale-up | 33.5 | 9.2 | 3.6 | $805K |
| SME | 39.5 | 9.6 | 4.1 | $950K |
| Mid-Market | 47.1 | 10.0 | 4.7 | $1.2M |
| Large Enterprise | 62.9 | 10.4 | 6.0 | $1.9M |
| Regulated | 100.0 | 12.6 | 7.9 | $4.2M |

### 100,000 LOC Codebase

| Organization | Effort (PM) | Schedule (mo) | People | Cost |
|--------------|-------------|---------------|--------|------|
| Early Startup | 160.0 | 17.5 | 9.1 | $3.0M |
| Growth Startup | 251.2 | 20.0 | 12.6 | $5.7M |
| Scale-up | 403.3 | 22.0 | 18.3 | $9.7M |
| SME | 497.3 | 23.0 | 21.6 | $11.9M |
| Mid-Market | 664.7 | 24.6 | 27.0 | $17.4M |
| Large Enterprise | 996.4 | 26.4 | 37.7 | $30.0M |
| Regulated | 1995.3 | 33.3 | 59.9 | $83.8M |

---

## scc Command Examples

### Using Built-in Project Types

```bash
# Organic (small team, familiar tech)
./bin/scc --cocomo-project-type organic -f json2 path/to/repo

# Semi-detached (medium complexity)
./bin/scc --cocomo-project-type semi-detached -f json2 path/to/repo

# Embedded (high reliability)
./bin/scc --cocomo-project-type embedded -f json2 path/to/repo
```

### Using Custom Coefficients

Format: `--cocomo-project-type "custom,a,b,c,d"`

```bash
# Early Startup
./bin/scc --cocomo-project-type "custom,2.0,1.00,2.2,0.40" \
          --avg-wage 150000 --overhead 1.5 --eaf 0.8 \
          -f json2 path/to/repo

# SME
./bin/scc --cocomo-project-type "custom,3.0,1.12,2.5,0.35" \
          --avg-wage 120000 --overhead 2.4 --eaf 1.0 \
          -f json2 path/to/repo

# Large Enterprise
./bin/scc --cocomo-project-type "custom,3.6,1.20,2.5,0.32" \
          --avg-wage 110000 --overhead 3.0 --eaf 1.2 \
          -f json2 path/to/repo

# Regulated Industry
./bin/scc --cocomo-project-type "custom,4.0,1.25,2.8,0.30" \
          --avg-wage 120000 --overhead 3.5 --eaf 1.5 \
          -f json2 path/to/repo
```

### JSON2 Output Format

```json
{
  "languageSummary": [...],
  "estimatedCost": 173711.06,
  "estimatedScheduleMonths": 7.07,
  "estimatedPeople": 2.18
}
```

---

## Interpretation Guidelines

### Cost Estimates Are Indicative

COCOMO estimates should be used as:
- **Order of magnitude** guidance, not precise budgets
- **Comparison tool** between presets/scenarios
- **Due diligence evidence** for effort assessment

### When to Use Each Preset

| If the target company is... | Use Preset |
|----------------------------|------------|
| A 5-person startup with 10K LOC | `early_startup` |
| A 50-person Series B with 50K LOC | `growth_startup` |
| A 200-person company with 100K LOC | `sme` |
| A Fortune 500 enterprise with 500K LOC | `large_enterprise` |
| A bank or healthcare company | `regulated` |

### Adjusting EAF

The Effort Adjustment Factor (EAF) can be adjusted based on:

| Factor | EAF Impact |
|--------|------------|
| Very experienced team | 0.7 - 0.9 |
| Modern tech stack | 0.8 - 0.95 |
| Complex domain (finance, healthcare) | 1.1 - 1.3 |
| Poor documentation | 1.2 - 1.5 |
| High regulatory requirements | 1.3 - 1.7 |
| Legacy technology | 1.2 - 1.6 |

---

## References

- Boehm, B. W. (1981). Software Engineering Economics. Prentice-Hall.
- COCOMO II Model Definition Manual (2000). USC CSE.
- scc documentation: https://github.com/boyter/scc
