"""Invariant checks for dotcover.

This module validates coverage data invariants:
- covered_statements <= total_statements at all levels
- 0 <= statement_coverage_pct <= 100 for all entities
- All statement counts >= 0
- Hierarchy consistency (methods reference valid types, types reference valid assemblies)
"""

from __future__ import annotations


def check_covered_lte_total(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that covered_statements <= total_statements at all levels."""
    results = []
    data = output.get("data", {})

    # Check summary level
    summary = data.get("summary", {})
    covered = summary.get("covered_statements", 0)
    total = summary.get("total_statements", 0)
    if covered > total:
        results.append({
            "check_id": "invariants.covered_lte_total.summary",
            "status": "fail",
            "message": f"Summary: covered ({covered}) > total ({total})",
        })
    else:
        results.append({
            "check_id": "invariants.covered_lte_total.summary",
            "status": "pass",
            "message": f"Summary: covered ({covered}) <= total ({total})",
        })

    # Check assemblies
    assemblies = data.get("assemblies", [])
    violations = []
    for asm in assemblies:
        covered = asm.get("covered_statements", 0)
        total = asm.get("total_statements", 0)
        if covered > total:
            violations.append(f"{asm.get('name', 'unknown')}: {covered} > {total}")

    if violations:
        results.append({
            "check_id": "invariants.covered_lte_total.assemblies",
            "status": "fail",
            "message": f"Assemblies with violations: {violations}",
        })
    else:
        results.append({
            "check_id": "invariants.covered_lte_total.assemblies",
            "status": "pass",
            "message": f"All {len(assemblies)} assemblies have covered <= total",
        })

    # Check types
    types = data.get("types", [])
    violations = []
    for t in types:
        covered = t.get("covered_statements", 0)
        total = t.get("total_statements", 0)
        if covered > total:
            violations.append(f"{t.get('name', 'unknown')}: {covered} > {total}")

    if violations:
        results.append({
            "check_id": "invariants.covered_lte_total.types",
            "status": "fail",
            "message": f"Types with violations: {violations[:5]}{'...' if len(violations) > 5 else ''}",
        })
    else:
        results.append({
            "check_id": "invariants.covered_lte_total.types",
            "status": "pass",
            "message": f"All {len(types)} types have covered <= total",
        })

    # Check methods
    methods = data.get("methods", [])
    violations = []
    for m in methods:
        covered = m.get("covered_statements", 0)
        total = m.get("total_statements", 0)
        if covered > total:
            violations.append(f"{m.get('name', 'unknown')}: {covered} > {total}")

    if violations:
        results.append({
            "check_id": "invariants.covered_lte_total.methods",
            "status": "fail",
            "message": f"Methods with violations: {violations[:5]}{'...' if len(violations) > 5 else ''}",
        })
    else:
        results.append({
            "check_id": "invariants.covered_lte_total.methods",
            "status": "pass",
            "message": f"All {len(methods)} methods have covered <= total",
        })

    return results


def check_percentage_bounds(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that 0 <= statement_coverage_pct <= 100 for all entities."""
    results = []
    data = output.get("data", {})

    def check_pct(entities: list[dict], level: str) -> dict:
        violations = []
        for entity in entities:
            pct = entity.get("statement_coverage_pct", 0)
            name = entity.get("name", "unknown")
            if pct < 0 or pct > 100:
                violations.append(f"{name}: {pct}%")

        if violations:
            return {
                "check_id": f"invariants.percentage_bounds.{level}",
                "status": "fail",
                "message": f"Out-of-bounds percentages: {violations[:5]}{'...' if len(violations) > 5 else ''}",
            }
        return {
            "check_id": f"invariants.percentage_bounds.{level}",
            "status": "pass",
            "message": f"All {len(entities)} {level} have valid percentage bounds",
        }

    # Check summary
    summary = data.get("summary", {})
    pct = summary.get("statement_coverage_pct", 0)
    if pct < 0 or pct > 100:
        results.append({
            "check_id": "invariants.percentage_bounds.summary",
            "status": "fail",
            "message": f"Summary coverage percentage out of bounds: {pct}%",
        })
    else:
        results.append({
            "check_id": "invariants.percentage_bounds.summary",
            "status": "pass",
            "message": f"Summary coverage percentage valid: {pct}%",
        })

    # Check each level
    results.append(check_pct(data.get("assemblies", []), "assemblies"))
    results.append(check_pct(data.get("types", []), "types"))
    results.append(check_pct(data.get("methods", []), "methods"))

    return results


def check_non_negative_counts(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that all statement counts are non-negative."""
    results = []
    data = output.get("data", {})

    def check_counts(entities: list[dict], level: str) -> dict:
        violations = []
        for entity in entities:
            covered = entity.get("covered_statements", 0)
            total = entity.get("total_statements", 0)
            name = entity.get("name", "unknown")
            if covered < 0:
                violations.append(f"{name}: covered={covered}")
            if total < 0:
                violations.append(f"{name}: total={total}")

        if violations:
            return {
                "check_id": f"invariants.non_negative_counts.{level}",
                "status": "fail",
                "message": f"Negative counts: {violations[:5]}{'...' if len(violations) > 5 else ''}",
            }
        return {
            "check_id": f"invariants.non_negative_counts.{level}",
            "status": "pass",
            "message": f"All {len(entities)} {level} have non-negative counts",
        }

    # Check summary
    summary = data.get("summary", {})
    covered = summary.get("covered_statements", 0)
    total = summary.get("total_statements", 0)
    if covered < 0 or total < 0:
        results.append({
            "check_id": "invariants.non_negative_counts.summary",
            "status": "fail",
            "message": f"Negative summary counts: covered={covered}, total={total}",
        })
    else:
        results.append({
            "check_id": "invariants.non_negative_counts.summary",
            "status": "pass",
            "message": f"Summary counts non-negative: covered={covered}, total={total}",
        })

    # Check each level
    results.append(check_counts(data.get("assemblies", []), "assemblies"))
    results.append(check_counts(data.get("types", []), "types"))
    results.append(check_counts(data.get("methods", []), "methods"))

    return results


def check_hierarchy_consistency(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check hierarchy consistency: methods reference valid types, types reference valid assemblies."""
    results = []
    data = output.get("data", {})

    # Build valid assembly names set
    assemblies = data.get("assemblies", [])
    valid_assemblies = {a.get("name") for a in assemblies if a.get("name")}

    # Build valid type names set (namespace.name or just name)
    types = data.get("types", [])
    valid_types = set()
    for t in types:
        name = t.get("name")
        if name:
            valid_types.add(name)
            # Also add with namespace if present
            namespace = t.get("namespace")
            if namespace:
                valid_types.add(f"{namespace}.{name}")

    # Check types reference valid assemblies
    type_violations = []
    for t in types:
        assembly = t.get("assembly")
        if assembly and assembly not in valid_assemblies:
            type_violations.append(f"{t.get('name', 'unknown')} -> {assembly}")

    if type_violations:
        results.append({
            "check_id": "invariants.hierarchy_consistency.types_to_assemblies",
            "status": "fail",
            "message": f"Types referencing invalid assemblies: {type_violations[:5]}{'...' if len(type_violations) > 5 else ''}",
        })
    else:
        results.append({
            "check_id": "invariants.hierarchy_consistency.types_to_assemblies",
            "status": "pass",
            "message": f"All {len(types)} types reference valid assemblies",
        })

    # Check methods reference valid types
    methods = data.get("methods", [])
    method_violations = []
    for m in methods:
        type_name = m.get("type_name")
        if type_name and type_name not in valid_types:
            method_violations.append(f"{m.get('name', 'unknown')} -> {type_name}")

    if method_violations:
        results.append({
            "check_id": "invariants.hierarchy_consistency.methods_to_types",
            "status": "fail",
            "message": f"Methods referencing invalid types: {method_violations[:5]}{'...' if len(method_violations) > 5 else ''}",
        })
    else:
        results.append({
            "check_id": "invariants.hierarchy_consistency.methods_to_types",
            "status": "pass",
            "message": f"All {len(methods)} methods reference valid types",
        })

    # Check methods reference valid assemblies
    method_asm_violations = []
    for m in methods:
        assembly = m.get("assembly")
        if assembly and assembly not in valid_assemblies:
            method_asm_violations.append(f"{m.get('name', 'unknown')} -> {assembly}")

    if method_asm_violations:
        results.append({
            "check_id": "invariants.hierarchy_consistency.methods_to_assemblies",
            "status": "fail",
            "message": f"Methods referencing invalid assemblies: {method_asm_violations[:5]}{'...' if len(method_asm_violations) > 5 else ''}",
        })
    else:
        results.append({
            "check_id": "invariants.hierarchy_consistency.methods_to_assemblies",
            "status": "pass",
            "message": f"All {len(methods)} methods reference valid assemblies",
        })

    return results
