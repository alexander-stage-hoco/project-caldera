"""Tests for stakeholder report profiles."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from insights.profiles import (
    StakeholderProfile,
    BUILTIN_PROFILES,
    CTO_PROFILE,
    INVESTOR_PROFILE,
    CEO_PROFILE,
    get_profile,
    list_profiles,
)
from insights.generator import InsightsGenerator


# ── Dataclass validation ────────────────────────────────────────────────────


class TestStakeholderProfileValidation:
    """Tests for StakeholderProfile __post_init__ validation."""

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name must not be empty"):
            StakeholderProfile(
                name="",
                display_name="X",
                description="X",
                sections=("a",),
                title_template="{repository}",
            )

    def test_empty_sections_raises(self):
        with pytest.raises(ValueError, match="at least one section"):
            StakeholderProfile(
                name="test",
                display_name="X",
                description="X",
                sections=(),
                title_template="{repository}",
            )

    def test_frozen_immutability(self):
        p = StakeholderProfile(
            name="test",
            display_name="X",
            description="X",
            sections=("a",),
            title_template="{repository}",
        )
        with pytest.raises(AttributeError):
            p.name = "changed"  # type: ignore[misc]

    def test_valid_profile_constructs(self):
        p = StakeholderProfile(
            name="custom",
            display_name="Custom",
            description="A custom profile",
            sections=("executive_summary", "composite_risk"),
            title_template="Custom: {repository}",
            gaps=("future_feature",),
        )
        assert p.name == "custom"
        assert p.gaps == ("future_feature",)

    def test_default_gaps_is_empty_tuple(self):
        p = StakeholderProfile(
            name="x",
            display_name="X",
            description="X",
            sections=("a",),
            title_template="{repository}",
        )
        assert p.gaps == ()


# ── Built-in profiles ───────────────────────────────────────────────────────


class TestBuiltinProfiles:
    """Tests for built-in profile constants."""

    def test_three_builtin_profiles(self):
        assert len(BUILTIN_PROFILES) == 3

    def test_builtin_names(self):
        names = {p.name for p in BUILTIN_PROFILES}
        assert names == {"cto", "investor", "ceo"}

    def test_get_profile_cto(self):
        assert get_profile("cto") is CTO_PROFILE

    def test_get_profile_investor(self):
        assert get_profile("investor") is INVESTOR_PROFILE

    def test_get_profile_ceo(self):
        assert get_profile("ceo") is CEO_PROFILE

    def test_get_profile_case_insensitive(self):
        assert get_profile("CTO") is CTO_PROFILE
        assert get_profile("Investor") is INVESTOR_PROFILE

    def test_get_profile_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown profile.*'nope'.*Available"):
            get_profile("nope")

    def test_list_profiles_returns_all(self):
        profiles = list_profiles()
        assert len(profiles) == 3
        assert all(isinstance(p, StakeholderProfile) for p in profiles)

    def test_cto_has_all_sections(self):
        """CTO profile should include all SECTIONS keys."""
        available = set(InsightsGenerator.SECTIONS.keys())
        cto_sections = set(CTO_PROFILE.sections)
        assert cto_sections == available, f"Mismatch: missing={available - cto_sections}, extra={cto_sections - available}"

    def test_investor_sections_subset_of_available(self):
        available = set(InsightsGenerator.SECTIONS.keys())
        assert set(INVESTOR_PROFILE.sections).issubset(available)

    def test_ceo_sections_subset_of_available(self):
        available = set(InsightsGenerator.SECTIONS.keys())
        assert set(CEO_PROFILE.sections).issubset(available)

    def test_investor_has_gaps(self):
        assert len(INVESTOR_PROFILE.gaps) > 0

    def test_ceo_has_gaps(self):
        assert len(CEO_PROFILE.gaps) > 0


# ── Section name validity ────────────────────────────────────────────────────


class TestSectionNameValidity:
    """Every section name in each profile must be a valid SECTIONS key."""

    @pytest.mark.parametrize("profile", BUILTIN_PROFILES, ids=lambda p: p.name)
    def test_all_section_names_valid(self, profile: StakeholderProfile):
        available = set(InsightsGenerator.SECTIONS.keys())
        invalid = set(profile.sections) - available
        assert not invalid, f"Profile {profile.name!r} references unknown sections: {invalid}"


# ── Generator integration ────────────────────────────────────────────────────


class TestGeneratorProfileIntegration:
    """Tests for profile support in InsightsGenerator.generate()."""

    @patch.object(InsightsGenerator, "__init__", lambda self, **kw: None)
    def _make_generator(self) -> InsightsGenerator:
        gen = InsightsGenerator.__new__(InsightsGenerator)
        gen.sections = {name: cls() for name, cls in InsightsGenerator.SECTIONS.items()}
        gen._evidence_builder = MagicMock()
        gen._formatters = {"md": MagicMock(), "html": MagicMock()}
        gen.fetcher = MagicMock()
        gen.fetcher.get_run_info.return_value = {"repository_name": "test-repo"}
        # Make formatter.format_report return a string
        for fmt in gen._formatters.values():
            fmt.format_report.return_value = "<report>"
            fmt.format_section.return_value = "<section>"
        return gen

    def test_profile_selects_sections(self):
        gen = self._make_generator()
        gen.generate(run_pk=1, format="md", profile="ceo", skip_validation=True)
        formatter = gen._formatters["md"]
        call_kwargs = formatter.format_report.call_args
        sections_rendered = [s.id for s in call_kwargs.kwargs["sections"]]
        # CEO profile has 5 sections
        assert set(sections_rendered) == set(CEO_PROFILE.sections)

    def test_profile_and_sections_raises(self):
        gen = self._make_generator()
        with pytest.raises(ValueError, match="Cannot specify both"):
            gen.generate(run_pk=1, profile="cto", sections=["executive_summary"], skip_validation=True)

    def test_profile_title_template_used(self):
        gen = self._make_generator()
        gen.generate(run_pk=1, format="md", profile="investor", skip_validation=True)
        formatter = gen._formatters["md"]
        call_kwargs = formatter.format_report.call_args
        assert call_kwargs.kwargs["title"] == "Investment Risk Assessment: test-repo"

    def test_explicit_title_overrides_profile(self):
        gen = self._make_generator()
        gen.generate(run_pk=1, format="md", profile="investor", title="Custom Title", skip_validation=True)
        formatter = gen._formatters["md"]
        call_kwargs = formatter.format_report.call_args
        assert call_kwargs.kwargs["title"] == "Custom Title"

    def test_metadata_includes_profile_name(self):
        gen = self._make_generator()
        gen.generate(run_pk=1, format="md", profile="ceo", skip_validation=True)
        formatter = gen._formatters["md"]
        call_kwargs = formatter.format_report.call_args
        assert call_kwargs.kwargs["metadata"]["profile"] == "ceo"

    def test_metadata_profile_none_when_no_profile(self):
        gen = self._make_generator()
        gen.generate(run_pk=1, format="md", skip_validation=True)
        formatter = gen._formatters["md"]
        call_kwargs = formatter.format_report.call_args
        assert call_kwargs.kwargs["metadata"]["profile"] is None

    def test_unknown_profile_string_raises(self):
        gen = self._make_generator()
        with pytest.raises(ValueError, match="Unknown profile"):
            gen.generate(run_pk=1, profile="nonexistent", skip_validation=True)

    def test_profile_object_accepted(self):
        gen = self._make_generator()
        gen.generate(run_pk=1, format="md", profile=CEO_PROFILE, skip_validation=True)
        formatter = gen._formatters["md"]
        call_kwargs = formatter.format_report.call_args
        assert call_kwargs.kwargs["metadata"]["profile"] == "ceo"


# ── CLI integration ──────────────────────────────────────────────────────────


class TestCLIProfileIntegration:
    """Tests for --profile option and list-profiles command in CLI."""

    def test_list_profiles_command(self):
        from typer.testing import CliRunner
        from insights.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["list-profiles"])
        assert result.exit_code == 0
        assert "cto" in result.output
        assert "investor" in result.output
        assert "ceo" in result.output

    def test_profile_and_sections_mutual_exclusion(self):
        from typer.testing import CliRunner
        from insights.cli import app

        runner = CliRunner()
        result = runner.invoke(app, [
            "generate", "1",
            "--db", "/tmp/nonexistent.duckdb",
            "--profile", "cto",
            "--sections", "executive_summary",
        ])
        assert result.exit_code == 1
        assert "Cannot specify both" in result.output
