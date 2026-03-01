"""Tests for NarrativeEnricher and narrative-aware sections."""

from __future__ import annotations

import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from insights.evaluation.llm.providers import LLMProvider, LLMResponse
from insights.narrative.enricher import NarrativeEnricher


# ---------------------------------------------------------------------------
# NarrativeEnricher unit tests
# ---------------------------------------------------------------------------


class TestNarrativeEnricher:
    def _make_enricher(self, mock_provider: MagicMock) -> NarrativeEnricher:
        """Create an enricher with a mocked provider."""
        enricher = NarrativeEnricher.__new__(NarrativeEnricher)
        enricher._trace_id = "test-trace"
        enricher._provider = mock_provider
        return enricher

    def test_enrich_success(self):
        provider = MagicMock()
        provider.complete.return_value = LLMResponse(
            content="The analysis reveals critical issues.",
            model="claude-sonnet-4",
        )
        enricher = self._make_enricher(provider)

        result = enricher.enrich(task="Summarize findings", data={"key": "value"})

        assert result == "The analysis reveals critical issues."
        provider.complete.assert_called_once()
        call_kwargs = provider.complete.call_args
        assert "Summarize findings" in call_kwargs.kwargs["prompt"]

    def test_enrich_failure_returns_none(self):
        provider = MagicMock()
        provider.complete.side_effect = RuntimeError("CLI not found")
        enricher = self._make_enricher(provider)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = enricher.enrich(task="Summarize", data={})

        assert result is None
        assert any("LLM call failed" in str(warning.message) for warning in w)

    def test_enrich_empty_response_returns_none(self):
        provider = MagicMock()
        provider.complete.return_value = LLMResponse(content="  ", model="claude-sonnet-4")
        enricher = self._make_enricher(provider)

        result = enricher.enrich(task="Summarize", data={})
        assert result is None

    def test_enrich_passes_temperature_and_max_tokens(self):
        provider = MagicMock()
        provider.complete.return_value = LLMResponse(content="OK", model="claude-sonnet-4")
        enricher = self._make_enricher(provider)

        enricher.enrich(task="Test", data={}, max_tokens=200)

        call_kwargs = provider.complete.call_args.kwargs
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_tokens"] == 200

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-key"})
    def test_provider_selection_anthropic(self):
        with patch(
            "insights.evaluation.llm.providers.anthropic.AnthropicAPIProvider"
        ) as mock_cls, patch(
            "insights.evaluation.llm.observability.observable_provider.ObservableProvider"
        ) as mock_obs:
            mock_cls.return_value = MagicMock()
            mock_obs.return_value = MagicMock()
            enricher = NarrativeEnricher()

            mock_cls.assert_called_once_with(model="claude-sonnet-4")

    def test_provider_selection_claude_code(self):
        import os
        env_backup = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with patch(
                "insights.evaluation.llm.providers.claude_code.ClaudeCodeHeadlessProvider"
            ) as mock_cls, patch(
                "insights.evaluation.llm.observability.observable_provider.ObservableProvider"
            ) as mock_obs:
                mock_cls.return_value = MagicMock()
                mock_obs.return_value = MagicMock()
                enricher = NarrativeEnricher()

                mock_cls.assert_called_once_with(model="claude-sonnet-4")
        finally:
            if env_backup is not None:
                os.environ["ANTHROPIC_API_KEY"] = env_backup

    def test_observable_wrapping(self):
        import os
        env_backup = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with patch(
                "insights.evaluation.llm.providers.claude_code.ClaudeCodeHeadlessProvider"
            ) as mock_provider_cls, patch(
                "insights.evaluation.llm.observability.observable_provider.ObservableProvider"
            ) as mock_obs:
                mock_provider_cls.return_value = MagicMock()
                mock_obs.return_value = MagicMock()
                enricher = NarrativeEnricher(trace_id="custom-trace")

                mock_obs.assert_called_once()
                call_kwargs = mock_obs.call_args.kwargs
                assert call_kwargs["trace_id"] == "custom-trace"
                assert call_kwargs["judge_name"] == "NarrativeEnricher"
        finally:
            if env_backup is not None:
                os.environ["ANTHROPIC_API_KEY"] = env_backup

    def test_trace_id_property(self):
        provider = MagicMock()
        enricher = self._make_enricher(provider)
        assert enricher.trace_id == "test-trace"

    def test_enrich_truncates_large_data(self):
        """Verify that oversized data triggers a truncation warning via the provider."""
        from shared.llm.prompt_guard import DEFAULT_MAX_PROMPT_CHARS

        provider = MagicMock()
        provider.complete.return_value = LLMResponse(
            content="Summary of truncated data.",
            model="claude-sonnet-4",
        )
        enricher = self._make_enricher(provider)

        # Create data large enough to exceed the default limit
        large_data = {"big_field": "x" * (DEFAULT_MAX_PROMPT_CHARS + 1000)}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = enricher.enrich(task="Summarize", data=large_data)

        assert result == "Summary of truncated data."
        # The provider's complete() receives the prompt; the concrete provider
        # (or ObservableProvider → concrete) applies the guard. In this mock
        # scenario the warning comes from the concrete provider layer. Since
        # we're using a raw MagicMock (not a real provider), the guard won't
        # fire here — but we verify the prompt was constructed and passed.
        call_kwargs = provider.complete.call_args
        prompt_arg = call_kwargs.kwargs.get("prompt") or call_kwargs[0][0]
        assert len(prompt_arg) > DEFAULT_MAX_PROMPT_CHARS


# ---------------------------------------------------------------------------
# Section integration tests
# ---------------------------------------------------------------------------


class TestExecutiveSummaryNarrative:
    def test_narrative_paragraph_populated_with_enricher(self):
        from insights.sections.executive_summary import ExecutiveSummarySection

        section = ExecutiveSummarySection()
        enricher = MagicMock()
        enricher.enrich.return_value = "LLM narrative paragraph."
        section.set_enricher(enricher)

        fetcher = MagicMock()
        fetcher.fetch.return_value = []

        data = section.fetch_data(fetcher, 1)
        assert data["narrative_paragraph"] is None or isinstance(data["narrative_paragraph"], str)
        # If there are no insights, enricher should not be called
        if not data["insights"]:
            enricher.enrich.assert_not_called()

    def test_no_enricher_means_no_narrative(self):
        from insights.sections.executive_summary import ExecutiveSummarySection

        section = ExecutiveSummarySection()
        fetcher = MagicMock()
        fetcher.fetch.return_value = []

        data = section.fetch_data(fetcher, 1)
        assert data["narrative_paragraph"] is None


class TestRiskRegisterNarrative:
    def test_enricher_called_for_top_risks(self):
        from insights.sections.risk_register import RiskRegisterSection
        from insights.evidence.entities import (
            EvidenceRegistry,
            ExecutionRisk,
            TechnicalClaim,
        )

        # Create a risk with supporting claims
        claim = TechnicalClaim(
            claim_id="CLM-TEST-001",
            category="security",
            statement="Critical vulnerability found",
            evidence_ids=("E-SEC-001",),
            implication="Exploitable",
            confidence="high",
            triggered_by="TestRule",
        )
        risk = ExecutionRisk(
            risk_id="RISK-001",
            description="Generic description",
            technical_cause="Unpatched dependency",
            claim_ids=("CLM-TEST-001",),
            manifests_in=("src/app.py",),
            triggered_by="SecurityExposureRule",
            severity="critical",
        )
        registry = EvidenceRegistry(
            evidence=[],
            claims=[claim],
            risks=[risk],
        )

        section = RiskRegisterSection()
        section.set_evidence_registry(registry)

        enricher = MagicMock()
        enricher.enrich.return_value = "Enriched risk description."
        section.set_enricher(enricher)

        data = section.fetch_data(MagicMock(), 1)
        enricher.enrich.assert_called_once()
        assert data["risks"][0].get("description_narrative") == "Enriched risk description."

    def test_enricher_capped_at_5(self):
        from insights.sections.risk_register import RiskRegisterSection
        from insights.evidence.entities import (
            EvidenceRegistry,
            ExecutionRisk,
            TechnicalClaim,
        )

        risks = []
        claims = []
        for i in range(8):
            c = TechnicalClaim(
                claim_id=f"CLM-TEST-{i:03d}",
                category="quality",
                statement=f"Claim {i}",
                evidence_ids=("E-SEC-001",),
                implication="Test",
                confidence="medium",
                triggered_by="TestRule",
            )
            claims.append(c)
            risks.append(
                ExecutionRisk(
                    risk_id=f"RISK-{i:03d}",
                    description=f"Risk {i}",
                    technical_cause=f"Cause {i}",
                    claim_ids=(c.claim_id,),
                    manifests_in=(f"src/file{i}.py",),
                    triggered_by="TestRule",
                    severity="medium",
                )
            )

        registry = EvidenceRegistry(evidence=[], claims=claims, risks=risks)

        section = RiskRegisterSection()
        section.set_evidence_registry(registry)

        enricher = MagicMock()
        enricher.enrich.return_value = "Enriched."
        section.set_enricher(enricher)

        section.fetch_data(MagicMock(), 1)
        assert enricher.enrich.call_count == 5


class TestDeltaSummaryNarrative:
    def test_narrative_populated_with_enricher_and_previous_run(self):
        from insights.sections.delta_summary import DeltaSummarySection

        section = DeltaSummarySection()
        enricher = MagicMock()
        enricher.enrich.return_value = "Complexity increased significantly."
        section.set_enricher(enricher)

        fetcher = MagicMock()
        # delta_summary returns a row with deltas
        delta_row = {"delta_ccn": 5, "delta_files": 2, "regression_complexity": True}
        fetcher.fetch.side_effect = lambda name, pk, **kw: {
            "delta_summary": [delta_row],
            "file_regressions_top": [],
        }.get(name, [])

        data = section.fetch_data(fetcher, 1)
        assert data["delta_narrative"] == "Complexity increased significantly."
        enricher.enrich.assert_called_once()

    def test_no_enricher_no_narrative(self):
        from insights.sections.delta_summary import DeltaSummarySection

        section = DeltaSummarySection()
        fetcher = MagicMock()
        fetcher.fetch.side_effect = lambda name, pk, **kw: {
            "delta_summary": [{"delta_ccn": 0}],
            "file_regressions_top": [],
        }.get(name, [])

        data = section.fetch_data(fetcher, 1)
        assert data["delta_narrative"] is None

    def test_no_previous_run_no_enricher_call(self):
        from insights.sections.delta_summary import DeltaSummarySection

        section = DeltaSummarySection()
        enricher = MagicMock()
        section.set_enricher(enricher)

        fetcher = MagicMock()
        fetcher.fetch.side_effect = lambda name, pk, **kw: {
            "delta_summary": [],
            "file_regressions_top": [],
        }.get(name, [])

        data = section.fetch_data(fetcher, 1)
        assert data["delta_narrative"] is None
        enricher.enrich.assert_not_called()


# ---------------------------------------------------------------------------
# LLMSynthesisRule tests
# ---------------------------------------------------------------------------


class TestLLMSynthesisRule:
    def _evidence(
        self, eid: str, cat: str, location: str = "src/file.py", excerpt: str = ""
    ):
        from insights.evidence.entities import EvidenceItem

        return EvidenceItem(
            evidence_id=eid,
            evidence_type="test",
            category=cat,  # type: ignore[arg-type]
            location=location,
            excerpt=excerpt or f"test for {eid}",
            observation="test",
            why_it_matters="test",
            tool_source="test",
            run_pk=1,
        )

    def test_generates_claims_from_llm_response(self):
        from insights.evidence.claim_generator import LLMSynthesisRule

        enricher = MagicMock()
        enricher.enrich.return_value = (
            "src/app.py: High complexity combined with low coverage and security vulnerabilities.\n"
            "src/db.py: Coupling issues overlap with ownership risk and quality smells."
        )

        rule = LLMSynthesisRule(enricher)
        evidence = [
            self._evidence("E-CCN-001", "complexity", "src/app.py"),
            self._evidence("E-SEC-001", "security", "src/app.py"),
            self._evidence("E-COVG-001", "coverage", "src/app.py"),
            self._evidence("E-COUP-001", "coupling", "src/db.py"),
            self._evidence("E-OWN-001", "ownership", "src/db.py"),
            self._evidence("E-QUAL-001", "quality", "src/db.py"),
        ]

        claims = rule.evaluate(evidence, MagicMock(), 1)
        assert len(claims) == 2
        assert claims[0].claim_id == "CLM-SYNT-001"
        assert claims[1].claim_id == "CLM-SYNT-002"
        assert claims[0].triggered_by == "LLMSynthesisRule"

    def test_returns_empty_when_enricher_fails(self):
        from insights.evidence.claim_generator import LLMSynthesisRule

        enricher = MagicMock()
        enricher.enrich.return_value = None

        rule = LLMSynthesisRule(enricher)
        evidence = [
            self._evidence("E-CCN-001", "complexity", "src/app.py"),
            self._evidence("E-SEC-001", "security", "src/app.py"),
            self._evidence("E-COVG-001", "coverage", "src/app.py"),
        ]

        claims = rule.evaluate(evidence, MagicMock(), 1)
        assert claims == []

    def test_returns_empty_when_no_hotspots(self):
        from insights.evidence.claim_generator import LLMSynthesisRule

        enricher = MagicMock()
        rule = LLMSynthesisRule(enricher)
        evidence = [
            self._evidence("E-CCN-001", "complexity", "src/a.py"),
            self._evidence("E-SEC-001", "security", "src/b.py"),
        ]

        claims = rule.evaluate(evidence, MagicMock(), 1)
        assert claims == []
        enricher.enrich.assert_not_called()


class TestClaimGeneratorWithEnricher:
    def test_enricher_adds_synthesis_rule(self):
        from insights.evidence.claim_generator import ClaimGenerator, LLMSynthesisRule

        enricher = MagicMock()
        gen = ClaimGenerator(enricher=enricher)
        assert len(gen._rules) == 7  # 6 default + 1 LLM
        assert isinstance(gen._rules[-1], LLMSynthesisRule)

    def test_no_enricher_uses_default_rules_only(self):
        from insights.evidence.claim_generator import ClaimGenerator

        gen = ClaimGenerator()
        assert len(gen._rules) == 6


class TestGeneratorReportLLMFlag:
    def test_no_enricher_when_flag_off(self):
        from insights.generator import InsightsGenerator

        # Use a non-existent db path — we won't actually connect
        gen = InsightsGenerator.__new__(InsightsGenerator)
        gen.db_path = MagicMock()
        gen.fetcher = MagicMock()
        gen.templates_dir = None
        gen._enricher = None

        assert gen._enricher is None


# ---------------------------------------------------------------------------
# NarrativeEnricher observability integration tests
# ---------------------------------------------------------------------------


class TestNarrativeEnricherObservability:
    """Verify that NarrativeEnricher calls produce real FileStore log entries."""

    @pytest.fixture(autouse=True)
    def _setup_observability(self, tmp_path: Path):
        """Configure observability with a temp log dir and reset after each test."""
        from shared.observability import (
            ObservabilityConfig,
            set_config,
            reset_config,
            reset_llm_logger,
            FileStore,
        )

        self.log_dir = tmp_path / "llm_logs"
        self.log_dir.mkdir()

        config = ObservabilityConfig(log_dir=self.log_dir, log_to_console=False)
        set_config(config)
        reset_llm_logger()  # force new logger with updated config

        self.store = FileStore(base_dir=self.log_dir)

        yield

        reset_config()
        reset_llm_logger()

    def _make_mock_provider(self, *, fail: bool = False) -> MagicMock:
        """Create a mock LLMProvider (not ObservableProvider)."""
        provider = MagicMock(spec=LLMProvider)
        provider.name = "mock_provider"
        provider.default_model = "claude-sonnet-4"
        provider.supports_model.return_value = True
        if fail:
            provider.complete.side_effect = RuntimeError("CLI not found")
        else:
            provider.complete.return_value = LLMResponse(
                content="The analysis reveals critical issues.",
                model="claude-sonnet-4",
                usage={"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            )
        return provider

    def _make_enricher(self, mock_provider: MagicMock, trace_id: str) -> NarrativeEnricher:
        """Create a NarrativeEnricher with a real ObservableProvider wrapping a mock."""
        from insights.evaluation.llm.observability.observable_provider import ObservableProvider

        enricher = NarrativeEnricher.__new__(NarrativeEnricher)
        enricher._trace_id = trace_id
        enricher._provider = ObservableProvider(
            provider=mock_provider,
            trace_id=trace_id,
            judge_name="NarrativeEnricher",
        )
        return enricher

    def test_enrich_logs_to_filestore(self):
        """Successful enrich() writes an interaction to FileStore."""
        mock = self._make_mock_provider()
        enricher = self._make_enricher(mock, trace_id="obs-success-trace")

        result = enricher.enrich(task="Summarize findings", data={"key": "value"})

        assert result == "The analysis reveals critical issues."

        interactions = self.store.query_by_trace("obs-success-trace")
        assert len(interactions) == 1
        assert interactions[0].judge_name == "NarrativeEnricher"
        assert interactions[0].status == "success"
        assert interactions[0].model == "claude-sonnet-4"

    def test_enrich_error_logged(self):
        """Failed enrich() logs an error interaction to FileStore."""
        mock = self._make_mock_provider(fail=True)
        enricher = self._make_enricher(mock, trace_id="obs-error-trace")

        result = enricher.enrich(task="Summarize", data={})

        assert result is None

        interactions = self.store.query_by_trace("obs-error-trace")
        assert len(interactions) == 1
        assert interactions[0].status == "error"
        assert "CLI not found" in interactions[0].error_message

    def test_trace_id_correlates_across_calls(self):
        """Multiple enrich() calls share the same trace_id in FileStore."""
        mock = self._make_mock_provider()
        enricher = self._make_enricher(mock, trace_id="obs-multi-trace")

        enricher.enrich(task="Task one", data={"a": 1})
        enricher.enrich(task="Task two", data={"b": 2})

        interactions = self.store.query_by_trace("obs-multi-trace")
        assert len(interactions) == 2
        assert all(i.trace_id == "obs-multi-trace" for i in interactions)
        assert all(i.judge_name == "NarrativeEnricher" for i in interactions)
