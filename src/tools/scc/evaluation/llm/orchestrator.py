"""LLM Evaluation Orchestrator for scc PoC.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of scc outputs.
"""

from __future__ import annotations

from pathlib import Path

from shared.evaluation import (
    LLMEvaluatorBase,
    DimensionResult,
    ProgrammaticInput,
    EvaluationResult,
)

from .judges.base import BaseJudge, JudgeResult


class LLMEvaluator(LLMEvaluatorBase):
    """Orchestrates LLM-based evaluation of scc outputs.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of output quality.
    """

    def __init__(
        self,
        working_dir: Path | None = None,
        model: str = "opus-4.5",
        results_dir: Path | None = None,
        timeout: int = 120,
    ):
        super().__init__(working_dir=working_dir, model=model, results_dir=results_dir)
        self.timeout = timeout

    def _default_results_dir(self) -> Path:
        """Override to use 'results' instead of 'llm/results'."""
        return self.working_dir / "evaluation" / "results"

    def register_all_judges(self) -> None:
        """Register all available judges."""
        from .judges.code_quality import CodeQualityJudge
        from .judges.integration_fit import IntegrationFitJudge
        from .judges.documentation import DocumentationJudge
        from .judges.edge_cases import EdgeCasesJudge
        from .judges.error_messages import ErrorMessagesJudge
        from .judges.api_design import APIDesignJudge
        from .judges.comparative import ComparativeJudge
        from .judges.risk import RiskJudge
        from .judges.directory_analysis import DirectoryAnalysisJudge
        from .judges.statistics import StatisticsJudge

        judges = [
            CodeQualityJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            IntegrationFitJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            DocumentationJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            EdgeCasesJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            ErrorMessagesJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            APIDesignJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            ComparativeJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            RiskJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            DirectoryAnalysisJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            StatisticsJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most important judges for quick evaluation."""
        from .judges.directory_analysis import DirectoryAnalysisJudge
        from .judges.statistics import StatisticsJudge
        from .judges.integration_fit import IntegrationFitJudge
        from .judges.api_design import APIDesignJudge

        judges = [
            DirectoryAnalysisJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            StatisticsJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            IntegrationFitJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
            APIDesignJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout),
        ]

        for judge in judges:
            self.register_judge(judge)

    def save_results(self, result: EvaluationResult) -> Path:
        """Save evaluation results to file."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.results_dir / "llm_evaluation.json"
        output_file.write_text(result.to_json())
        return output_file
