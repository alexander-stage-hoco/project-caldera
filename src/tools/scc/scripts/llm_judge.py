"""LLM-as-Judge for qualitative evaluation dimensions."""

import json
import os
from typing import Optional, Dict, Any
from pathlib import Path


# Check if anthropic is available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


JUDGE_PROMPT_TEMPLATE = """You are evaluating a code analysis tool (scc) for integration into a Due Diligence platform.

## Context
{context}

## Evaluation Dimension: {dimension}

## Evidence
{evidence}

## Task
Rate this dimension on a scale of 1-5:
- 5: Excellent - exceeds expectations
- 4: Good - meets all requirements
- 3: Acceptable - meets minimum requirements
- 2: Poor - significant gaps
- 1: Unacceptable - fails requirements

Provide:
1. Score (1-5)
2. Reasoning (2-3 sentences)
3. Specific evidence cited

Respond in JSON format:
{{"score": N, "reasoning": "...", "evidence": ["..."]}}
"""


def get_client() -> Optional[Any]:
    """Get Anthropic client if available."""
    if not ANTHROPIC_AVAILABLE:
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    return anthropic.Anthropic(api_key=api_key)


def judge_dimension(
    dimension: str,
    context: str,
    evidence: Dict[str, Any],
    model: str = "claude-3-haiku-20240307"
) -> Dict[str, Any]:
    """Use LLM to judge a qualitative dimension."""
    client = get_client()

    if not client:
        return {
            "score": None,
            "reasoning": "LLM evaluation skipped (no API key or anthropic not installed)",
            "evidence": [],
            "llm_available": False
        }

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        context=context,
        dimension=dimension,
        evidence=json.dumps(evidence, indent=2)
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        content = response.content[0].text
        # Find JSON in response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(content[start:end])
            result["llm_available"] = True
            return result

        return {
            "score": None,
            "reasoning": f"Could not parse LLM response: {content[:100]}",
            "evidence": [],
            "llm_available": True
        }

    except Exception as e:
        return {
            "score": None,
            "reasoning": f"LLM error: {str(e)}",
            "evidence": [],
            "llm_available": True,
            "error": str(e)
        }


def judge_output_richness(raw_output: list) -> Dict[str, Any]:
    """Judge the richness and comprehensiveness of scc output."""
    context = """
    scc (Sloc Cloc Code) is a code metrics tool that analyzes repositories.
    We are evaluating whether its output provides sufficient detail for
    technical due diligence purposes.
    """

    evidence = {
        "fields_per_language": list(raw_output[0].keys()) if raw_output else [],
        "languages_detected": len(raw_output),
        "sample_entry": raw_output[0] if raw_output else {},
        "has_complexity": any("Complexity" in entry for entry in raw_output),
        "has_bytes": any("Bytes" in entry for entry in raw_output),
        "has_file_breakdown": any("Files" in entry for entry in raw_output)
    }

    return judge_dimension("Output Richness", context, evidence)


def judge_transformation_elegance(transform_code: str, evidence_output: dict) -> Dict[str, Any]:
    """Judge how clean and elegant the transformation is."""
    context = """
    We are transforming scc JSON output to our evidence schema format.
    A good transformation should be straightforward, minimal, and maintain data integrity.
    """

    evidence = {
        "transform_code_lines": len(transform_code.split("\n")),
        "fields_mapped": len(evidence_output.get("items", [{}])[0].get("data", {}).keys()) if evidence_output.get("items") else 0,
        "has_provenance": "provenance" in (evidence_output.get("items", [{}])[0] if evidence_output.get("items") else {}),
        "has_summary": "summary" in evidence_output
    }

    return judge_dimension("Transformation Elegance", context, evidence)


def judge_documentation_quality(readme_path: Path) -> Dict[str, Any]:
    """Judge the quality of README documentation."""
    context = """
    We are evaluating whether the scc tool has good documentation
    for integration and usage in our platform.
    """

    try:
        with open(readme_path) as f:
            readme_content = f.read()

        evidence = {
            "readme_length": len(readme_content),
            "has_installation": "install" in readme_content.lower(),
            "has_usage": "usage" in readme_content.lower() or "example" in readme_content.lower(),
            "has_options": "--" in readme_content or "options" in readme_content.lower(),
            "has_license": "license" in readme_content.lower() or "mit" in readme_content.lower()
        }
    except FileNotFoundError:
        evidence = {
            "readme_exists": False,
            "error": "README not found"
        }

    return judge_dimension("Documentation Quality", context, evidence)


def run_llm_judgments(base_path: Path) -> Dict[str, Dict[str, Any]]:
    """Run all LLM judgments and return results."""
    results = {}

    # Load data for judgments
    raw_output_path = base_path / "output" / "raw_scc_output.json"
    evidence_path = base_path / "output" / "evidence_output.json"
    transform_path = base_path / "scripts" / "transform.py"
    readme_path = base_path / "README.md"

    try:
        with open(raw_output_path) as f:
            raw_output = json.load(f)
    except Exception:
        raw_output = []

    try:
        with open(evidence_path) as f:
            evidence_output = json.load(f)
    except Exception:
        evidence_output = {}

    try:
        with open(transform_path) as f:
            transform_code = f.read()
    except Exception:
        transform_code = ""

    # Run judgments
    results["output_richness"] = judge_output_richness(raw_output)
    results["transformation_elegance"] = judge_transformation_elegance(transform_code, evidence_output)
    results["documentation_quality"] = judge_documentation_quality(readme_path)

    return results
