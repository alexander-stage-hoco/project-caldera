"""Shared base judge class for LLM-as-a-Judge evaluation.

This module provides a standardized BaseJudge implementation for use across
all Project Caldera analysis tools. Each tool's LLM judges should inherit
from this class.

Observability is automatically integrated - all LLM invocations are logged
to the observability module for debugging and analysis.
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# Import shared LLM client
from shared.llm import (
    LLMClient,
    MODEL_MAP as _LLM_MODEL_MAP,
    CLI_MODEL_MAP as _LLM_CLI_MODEL_MAP,
    HAS_ANTHROPIC_SDK,
    validate_claude_cli as _validate_claude_cli,
)

# Import observability module
try:
    from shared.observability import (
        get_llm_logger,
        LLMLogger,
        get_config as get_observability_config,
    )
    HAS_OBSERVABILITY = True
except ImportError:
    HAS_OBSERVABILITY = False
    get_llm_logger = None  # type: ignore
    LLMLogger = None  # type: ignore
    get_observability_config = None  # type: ignore


@dataclass
class JudgeResult:
    """Result from an LLM judge evaluation.

    Attributes:
        dimension: Name of the evaluation dimension (e.g., "coverage", "accuracy")
        score: Numeric score from 1-5 (1=poor, 5=excellent)
        confidence: Confidence level from 0.0-1.0
        reasoning: Explanation of the score
        evidence_cited: List of evidence points used in evaluation
        recommendations: List of improvement recommendations
        sub_scores: Dictionary of sub-dimension scores
        raw_response: The raw LLM response text
    """

    dimension: str
    score: int  # 1-5
    confidence: float  # 0.0-1.0
    reasoning: str
    evidence_cited: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    sub_scores: dict[str, int] = field(default_factory=dict)
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JudgeResult:
        """Create JudgeResult from dictionary.

        Args:
            data: Dictionary with JudgeResult fields

        Returns:
            JudgeResult instance
        """
        return cls(
            dimension=data.get("dimension", "unknown"),
            score=data.get("score", 0),
            confidence=data.get("confidence", 0.0),
            reasoning=data.get("reasoning", ""),
            evidence_cited=data.get("evidence_cited", []),
            recommendations=data.get("recommendations", []),
            sub_scores=data.get("sub_scores", {}),
            raw_response=data.get("raw_response", ""),
        )

    def is_passing(self, threshold: int = 3) -> bool:
        """Check if the score meets the passing threshold.

        Args:
            threshold: Minimum passing score (default 3)

        Returns:
            True if score >= threshold
        """
        return self.score >= threshold


class BaseJudge(ABC):
    """Base class for LLM judges.

    Each judge evaluates a specific dimension of tool output quality.
    Judges can invoke Claude via the Anthropic SDK (preferred) or
    Claude Code CLI (fallback).

    Subclasses must implement:
        - dimension_name: Property returning the dimension name
        - weight: Property returning the dimension weight (0.0-1.0)
        - collect_evidence(): Method to gather evidence for evaluation
        - get_default_prompt(): Method returning the default prompt template

    Example:
        class AccuracyJudge(BaseJudge):
            @property
            def dimension_name(self) -> str:
                return "accuracy"

            @property
            def weight(self) -> float:
                return 0.35

            def collect_evidence(self) -> dict[str, Any]:
                return {...}

            def get_default_prompt(self) -> str:
                return "..."
    """

    # Model name to API ID mapping (for SDK/logging)
    # Re-exported from shared.llm for backward compatibility
    MODEL_MAP = _LLM_MODEL_MAP

    # Model name to CLI alias mapping (CLI doesn't understand "opus-4.5")
    # Re-exported from shared.llm for backward compatibility
    CLI_MODEL_MAP = _LLM_CLI_MODEL_MAP

    # Known synthetic repo patterns for auto-detection
    SYNTHETIC_PATTERNS = {
        "api-keys", "aws-credentials", "database-creds", "private-keys",
        "no-secrets", "mixed-secrets", "historical-secrets", "cloud-mixed",
        "synthetic", "vulnerable-npm", "clean-npm", "null-safety",
        "async-patterns", "resource-management", "api-conventions",
    }

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        output_dir: Path | None = None,
        ground_truth_dir: Path | None = None,
        use_llm: bool = True,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,
    ):
        """Initialize the judge.

        Args:
            model: Model name ("sonnet", "opus", "opus-4.5", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            output_dir: Directory containing analysis output files
            ground_truth_dir: Directory containing ground truth files
            use_llm: Whether to use LLM evaluation (False for heuristic-only)
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions (default True)
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
        self.model = model
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd()
        self.output_dir = output_dir or self.working_dir / "output" / "runs"
        self.ground_truth_dir = ground_truth_dir or self.working_dir / "evaluation" / "ground-truth"
        self.use_llm = use_llm
        self._prompt_template: str | None = None
        self._evaluation_mode = evaluation_mode

        # Observability
        self._trace_id = trace_id or str(uuid.uuid4())
        self._enable_observability = enable_observability and HAS_OBSERVABILITY
        self._logger: LLMLogger | None = None

        # Initialize logger if observability is enabled
        if self._enable_observability and get_llm_logger is not None:
            config = get_observability_config()
            if config and config.enabled:
                self._logger = get_llm_logger()

        # Initialize LLM client for invocations
        self._llm_client = LLMClient(
            model=model,
            timeout=timeout,
            working_dir=self.working_dir,
        )

    @property
    def trace_id(self) -> str:
        """Get the trace ID for this judge."""
        return self._trace_id

    @property
    def evaluation_mode(self) -> str:
        """Detect whether we're evaluating synthetic or real-world repos.

        Returns:
            "synthetic" if evaluating repos with known ground truth
            "real_world" if evaluating production/real-world repos
        """
        if self._evaluation_mode:
            return self._evaluation_mode

        # Auto-detect based on output directory structure
        # Synthetic repos have known scenario names; real-world repos have UUIDs or repo names
        if self.output_dir.exists():
            subdirs = {d.name for d in self.output_dir.iterdir() if d.is_dir()}
            # Also check for JSON files with synthetic pattern names
            json_stems = {f.stem for f in self.output_dir.glob("*.json") if not f.name.startswith(".")}
            all_names = subdirs | json_stems

            if any(pattern in all_names for pattern in self.SYNTHETIC_PATTERNS):
                return "synthetic"

        return "real_world"

    def load_synthetic_evaluation_context(self) -> dict[str, Any] | None:
        """Load evaluation results from synthetic repo runs.

        Returns summary of tool performance on synthetic repos with known ground truth.
        This provides baseline context for evaluating real-world repos.

        Returns:
            Dictionary with synthetic evaluation summary, or None if not available.
        """
        # Look for evaluation_report.json in the evaluation results directory
        eval_report_path = self.working_dir / "evaluation" / "results" / "evaluation_report.json"
        if not eval_report_path.exists():
            return None

        try:
            report = json.loads(eval_report_path.read_text())
        except (json.JSONDecodeError, OSError):
            return None

        # Extract relevant fields for context
        checks = report.get("checks", [])
        validated_capabilities = [
            check["name"] for check in checks
            if check.get("status") == "PASS"
        ]
        failed_checks = [
            check["name"] for check in checks
            if check.get("status") == "FAIL"
        ]

        return {
            "tool": report.get("tool", "unknown"),
            "synthetic_score": report.get("score", 0.0),
            "decision": report.get("decision", "UNKNOWN"),
            "checks_summary": report.get("summary", {}),
            "categories": report.get("categories", {}),
            "validated_capabilities": validated_capabilities,
            "failed_checks": failed_checks,
            "timestamp": report.get("timestamp", ""),
        }

    def get_interpretation_guidance(self, synthetic_context: dict[str, Any]) -> str:
        """Generate interpretation guidance based on synthetic context.

        Args:
            synthetic_context: Results from load_synthetic_evaluation_context()

        Returns:
            Guidance string to include in evidence for the LLM.
        """
        score = synthetic_context.get("synthetic_score", 0.0)
        decision = synthetic_context.get("decision", "UNKNOWN")
        validated = synthetic_context.get("validated_capabilities", [])

        if score >= 0.9:
            quality = "fully validated"
        elif score >= 0.7:
            quality = "mostly validated"
        else:
            quality = "partially validated"

        guidance = (
            f"This tool has been {quality} against synthetic repos with known issues. "
            f"Synthetic evaluation: {score:.0%} score ({decision}). "
            f"Validated capabilities: {len(validated)}. "
        )

        if score >= 0.9:
            guidance += (
                "Low or zero finding counts on this real-world repo likely indicate a clean "
                "codebase, NOT tool failure. Score based on output quality and schema "
                "compliance, not finding count."
            )
        elif score >= 0.7:
            guidance += (
                "The tool has demonstrated capability but has some gaps. "
                "Consider both output quality and detection capability when scoring."
            )
        else:
            guidance += (
                "The tool has known detection gaps. "
                "Lower scores may be appropriate even for output quality issues."
            )

        return guidance

    @classmethod
    def validate_claude_cli(cls) -> tuple[bool, str]:
        """Check if Claude CLI is available and executable.

        Returns:
            Tuple of (is_valid, message). If valid, message contains the path.
            If invalid, message contains the error reason.
        """
        return _validate_claude_cli()

    @property
    @abstractmethod
    def dimension_name(self) -> str:
        """Name of the evaluation dimension (e.g., 'accuracy', 'coverage')."""
        ...

    @property
    @abstractmethod
    def weight(self) -> float:
        """Weight of this dimension in the overall score (0.0-1.0)."""
        ...

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file.

        Override this property to customize the prompt location.
        Default location is `../prompts/{dimension_name}.md` relative
        to the judge module.
        """
        return Path(__file__).parent / "prompts" / f"{self.dimension_name}.md"

    def load_prompt_template(self) -> str:
        """Load the prompt template from file.

        First tries to load from prompt_file. If not found, falls back
        to get_default_prompt().

        Returns:
            The prompt template string
        """
        if self._prompt_template is None:
            if self.prompt_file.exists():
                self._prompt_template = self.prompt_file.read_text()
            else:
                self._prompt_template = self.get_default_prompt()
        return self._prompt_template

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist.

        Subclasses should override this to provide a dimension-specific
        default prompt. The template should include `{{ evidence }}`
        placeholder for evidence injection.

        Returns:
            Default prompt template string
        """
        return f"""# {self.dimension_name.replace('_', ' ').title()} Evaluation

Evaluate the following evidence and provide a score from 1-5.

## Evidence

{{{{ evidence }}}}

## Response Format

Respond with ONLY a JSON object:

{{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<explanation>",
  "evidence_cited": ["<evidence points>"],
  "recommendations": ["<improvements>"],
  "sub_scores": {{}}
}}
"""

    @abstractmethod
    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence files and data for evaluation.

        Returns:
            Dictionary containing all evidence for the evaluation.
            This will be JSON-serialized and injected into the prompt.
        """
        ...

    def load_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir.

        Returns:
            Dictionary keyed by repo name to analysis data.
            Uses 'id' field from envelope if present, otherwise filename stem.
        """
        results = {}

        if self.output_dir.exists() and self.output_dir.is_dir():
            json_files = list(self.output_dir.glob("*.json"))
            for json_file in sorted(json_files):
                if json_file.name.startswith("."):
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    # Use 'id' field from envelope for ground truth matching,
                    # fall back to filename stem
                    repo_name = data.get("id", json_file.stem)
                    # Handle envelope format
                    if "data" in data:
                        results[repo_name] = data.get("data", {})
                    elif "results" in data:
                        results[repo_name] = data
                    else:
                        results[repo_name] = data
                except json.JSONDecodeError:
                    continue

        return results

    def load_ground_truth(self) -> dict[str, Any]:
        """Load all ground truth files.

        Returns:
            Dictionary keyed by repo name to ground truth data.
        """
        results = {}

        if self.ground_truth_dir.exists():
            for gt_file in sorted(self.ground_truth_dir.glob("*.json")):
                if gt_file.name.startswith("."):
                    continue
                try:
                    data = json.loads(gt_file.read_text())
                    # Use 'id' field if present, otherwise filename stem
                    repo_name = data.get("id", gt_file.stem)
                    results[repo_name] = data
                except json.JSONDecodeError:
                    continue

        return results

    @staticmethod
    def extract_files(analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract files list from analysis data, handling multiple formats.

        Supports:
            - data["results"]["files"] (current format)
            - data["data"]["files"] (envelope format, e.g., semgrep)
            - data["files"] (legacy format)

        Args:
            analysis: Analysis data dictionary

        Returns:
            List of file dictionaries
        """
        # Try current format first (results.files)
        if "results" in analysis and isinstance(analysis["results"], dict):
            return analysis["results"].get("files", [])
        # Try envelope format (data.files) - used by semgrep and similar tools
        if "data" in analysis and isinstance(analysis["data"], dict):
            return analysis["data"].get("files", [])
        # Fallback to legacy format (direct files)
        return analysis.get("files", [])

    @staticmethod
    def extract_summary(analysis: dict[str, Any]) -> dict[str, Any]:
        """Extract summary dict from analysis data, handling multiple formats.

        Supports:
            - data["results"]["summary"] (current format)
            - data["data"]["summary"] (envelope format, e.g., semgrep)
            - data["summary"] (legacy format)

        Args:
            analysis: Analysis data dictionary

        Returns:
            Summary dictionary
        """
        # Try current format first (results.summary)
        if "results" in analysis and isinstance(analysis["results"], dict):
            return analysis["results"].get("summary", {})
        # Try envelope format (data.summary) - used by semgrep and similar tools
        if "data" in analysis and isinstance(analysis["data"], dict):
            return analysis["data"].get("summary", {})
        # Fallback to legacy format (direct summary)
        return analysis.get("summary", {})

    def build_prompt(self, evidence: dict[str, Any]) -> str:
        """Build the complete prompt with evidence.

        Supports two placeholder patterns:
        1. {{ evidence }} - replaced with entire evidence dict as JSON
        2. {{ key_name }} - replaced with specific evidence[key_name] as JSON

        Args:
            evidence: Evidence dictionary from collect_evidence()

        Returns:
            Complete prompt string ready for LLM invocation
        """
        template = self.load_prompt_template()

        # Replace {{ evidence }} with entire dict if present
        evidence_str = json.dumps(evidence, indent=2, default=str)
        prompt = template.replace("{{ evidence }}", evidence_str)

        # Replace individual {{ key }} placeholders with their values
        for key, value in evidence.items():
            placeholder = "{{ " + key + " }}"
            if placeholder in prompt:
                value_str = json.dumps(value, indent=2, default=str)
                prompt = prompt.replace(placeholder, value_str)

        # Check for unresolved placeholders
        if "{{" in prompt and "}}" in prompt:
            # Find the unresolved placeholder for better error message
            import re
            unresolved = re.findall(r"\{\{\s*\w+\s*\}\}", prompt)
            raise ValueError(f"Unresolved prompt placeholders: {unresolved}")

        if "Respond with ONLY a JSON object" not in prompt:
            prompt = (
                prompt
                + "\n\nRespond with ONLY a JSON object. Do not use markdown fences or extra text."
            )
        return prompt

    def parse_response(self, response: str) -> JudgeResult:
        """Parse the LLM response into a structured result.

        First attempts to extract JSON from the response. If JSON parsing
        fails, falls back to extracting score from text patterns.

        Args:
            response: Raw LLM response text

        Returns:
            JudgeResult with parsed data
        """
        try:
            # Try to extract JSON from the response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                result = JudgeResult.from_dict(data)
                result.dimension = self.dimension_name
                result.raw_response = response
                return result
        except json.JSONDecodeError:
            pass

        # Fallback: extract score from text
        score = 3  # Default to middle score
        for i in range(5, 0, -1):
            if f"score: {i}" in response.lower() or f"score:{i}" in response.lower():
                score = i
                break

        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=0.5,
            reasoning=response[:500] if response else "No response received",
            raw_response=response,
        )

    def invoke_claude(self, prompt: str) -> str:
        """Invoke Claude, preferring SDK and falling back to CLI.

        All invocations are logged to the observability module when enabled.
        Uses the shared LLMClient for actual invocation.

        Args:
            prompt: The prompt to send

        Returns:
            Response text
        """
        interaction_id: str | None = None

        # Start observability logging
        if self._logger is not None:
            interaction_id = self._logger.start_interaction(
                trace_id=self._trace_id,
                provider_name="anthropic_sdk" if HAS_ANTHROPIC_SDK else "claude_cli",
                judge_name=self.dimension_name,
                model=self.MODEL_MAP.get(self.model, self.model),
                user_prompt=prompt,
            )

        try:
            # Use LLMClient for invocation
            response = self._llm_client.invoke(prompt)

            # Log based on response status
            if self._llm_client.is_error_response(response):
                if self._llm_client.is_timeout_error(response):
                    if self._logger is not None and interaction_id:
                        self._logger.log_timeout(interaction_id, self.timeout)
                else:
                    if self._logger is not None and interaction_id:
                        self._logger.complete_interaction(
                            interaction_id=interaction_id,
                            response_content=response,
                            status="error",
                            error_message=response,
                        )
            else:
                if self._logger is not None and interaction_id:
                    self._logger.complete_interaction(
                        interaction_id=interaction_id,
                        response_content=response,
                        status="success",
                    )

            return response

        except Exception as e:
            # Log any unexpected errors
            if self._logger is not None and interaction_id:
                self._logger.log_error(interaction_id, e)
            raise

    def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
        """Run heuristic-based evaluation without LLM.

        Override this method in subclasses to provide dimension-specific
        heuristic evaluation logic. The default implementation returns
        a neutral score.

        Args:
            evidence: Evidence dictionary from collect_evidence()

        Returns:
            JudgeResult with heuristic-based scoring
        """
        return JudgeResult(
            dimension=self.dimension_name,
            score=3,
            confidence=0.6,
            reasoning="Heuristic evaluation not implemented for this dimension",
            evidence_cited=[],
            recommendations=["Implement run_heuristic_evaluation() for this judge"],
            raw_response="",
        )

    def evaluate(self) -> JudgeResult:
        """Run the full evaluation pipeline.

        If use_llm is False, runs heuristic evaluation only.
        Otherwise, collects evidence, builds prompt, invokes Claude,
        and parses the response.

        Returns:
            JudgeResult with evaluation outcome
        """
        # Collect evidence
        evidence = self.collect_evidence()

        # Check if we should use heuristic evaluation
        if not self.use_llm:
            return self.run_heuristic_evaluation(evidence)

        # Build prompt
        try:
            prompt = self.build_prompt(evidence)
        except ValueError as exc:
            return JudgeResult(
                dimension=self.dimension_name,
                score=1,
                confidence=0.0,
                reasoning=str(exc),
                evidence_cited=[],
                recommendations=["Fix prompt placeholders before evaluation"],
                raw_response="",
            )

        # Invoke Claude
        response = self.invoke_claude(prompt)

        # Parse response
        result = self.parse_response(response)

        return result

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation.

        Override this method in subclasses to add pre-evaluation
        validation checks.

        Returns:
            Tuple of (all_passed, list of failure messages)
        """
        # Default: no assertions, always pass
        return True, []

    # Legacy interface support
    def get_prompt(self, data: dict) -> str:
        """Generate the evaluation prompt (legacy interface).

        Deprecated: Use build_prompt() instead.

        Args:
            data: Evidence dictionary

        Returns:
            Prompt string
        """
        return self.build_prompt(data)
