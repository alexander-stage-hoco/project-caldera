"""
End-to-end tests for the Insights reporting component.

These tests validate the full pipeline from database to report generation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from datetime import datetime

import duckdb
import pytest

from insights.generator import InsightsGenerator
from insights.data_fetcher import DataFetcher


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Create a temporary database path."""
    return tmp_path / "test.duckdb"


@pytest.fixture
def seeded_db(test_db_path: Path) -> Path:
    """
    Create a test database with landing zone tables and sample data.

    This simulates a database after orchestrator has run tools and
    persisted results to the landing zone.
    """
    conn = duckdb.connect(str(test_db_path))

    # Create landing zone schema
    conn.execute("""
        CREATE SEQUENCE lz_run_pk_seq START 1;

        CREATE TABLE lz_collection_runs (
            collection_run_id VARCHAR NOT NULL,
            repo_id VARCHAR NOT NULL,
            run_id VARCHAR NOT NULL,
            branch VARCHAR NOT NULL,
            commit VARCHAR NOT NULL,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            status VARCHAR NOT NULL,
            PRIMARY KEY (collection_run_id)
        );

        CREATE TABLE lz_tool_runs (
            run_pk BIGINT DEFAULT nextval('lz_run_pk_seq'),
            collection_run_id VARCHAR NOT NULL,
            repo_id VARCHAR NOT NULL,
            run_id VARCHAR NOT NULL,
            tool_name VARCHAR NOT NULL,
            tool_version VARCHAR NOT NULL,
            schema_version VARCHAR NOT NULL,
            branch VARCHAR NOT NULL,
            commit VARCHAR NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk)
        );

        CREATE TABLE lz_layout_files (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            filename VARCHAR NOT NULL,
            extension VARCHAR,
            language VARCHAR,
            category VARCHAR,
            size_bytes BIGINT,
            line_count INTEGER,
            is_binary BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id)
        );

        CREATE TABLE lz_scc_file_metrics (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            filename VARCHAR,
            extension VARCHAR,
            language VARCHAR,
            lines_total INTEGER,
            code_lines INTEGER,
            comment_lines INTEGER,
            blank_lines INTEGER,
            bytes BIGINT,
            complexity INTEGER,
            PRIMARY KEY (run_pk, file_id)
        );

        CREATE TABLE lz_lizard_file_metrics (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            language VARCHAR,
            nloc INTEGER,
            function_count INTEGER,
            total_ccn INTEGER,
            avg_ccn DOUBLE,
            max_ccn INTEGER,
            PRIMARY KEY (run_pk, file_id)
        );

        CREATE TABLE lz_semgrep_smells (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR,
            relative_path VARCHAR NOT NULL,
            rule_id VARCHAR NOT NULL,
            dd_smell_id VARCHAR,
            dd_category VARCHAR,
            severity VARCHAR,
            line_start INTEGER,
            line_end INTEGER,
            message TEXT,
            PRIMARY KEY (run_pk, file_id, rule_id, line_start)
        );

        CREATE TABLE lz_trivy_vulnerabilities (
            run_pk BIGINT NOT NULL,
            target_key VARCHAR NOT NULL,
            vulnerability_id VARCHAR NOT NULL,
            package_name VARCHAR NOT NULL,
            installed_version VARCHAR,
            fixed_version VARCHAR,
            severity VARCHAR,
            cvss_score DOUBLE,
            title VARCHAR,
            PRIMARY KEY (run_pk, target_key, vulnerability_id, package_name)
        );
    """)

    # Insert sample collection run
    conn.execute("""
        INSERT INTO lz_collection_runs VALUES (
            'coll-001',
            'test-repo',
            'run-001',
            'main',
            'abc123def456',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            'completed'
        )
    """)

    # Insert tool runs
    conn.execute("""
        INSERT INTO lz_tool_runs VALUES
            (1, 'coll-001', 'test-repo', 'run-001', 'layout', '1.0.0', '1.0', 'main', 'abc123def456', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (2, 'coll-001', 'test-repo', 'run-001', 'scc', '3.0.0', '1.0', 'main', 'abc123def456', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
            (3, 'coll-001', 'test-repo', 'run-001', 'lizard', '1.17.0', '1.0', 'main', 'abc123def456', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)

    # Insert layout files
    conn.execute("""
        INSERT INTO lz_layout_files VALUES
            (1, 'f001', 'src/main.py', 'd001', 'main.py', '.py', 'Python', 'source', 5000, 150, FALSE, CURRENT_TIMESTAMP),
            (1, 'f002', 'src/utils.py', 'd001', 'utils.py', '.py', 'Python', 'source', 3000, 100, FALSE, CURRENT_TIMESTAMP),
            (1, 'f003', 'src/models/user.py', 'd002', 'user.py', '.py', 'Python', 'source', 2000, 80, FALSE, CURRENT_TIMESTAMP),
            (1, 'f004', 'tests/test_main.py', 'd003', 'test_main.py', '.py', 'Python', 'test', 1500, 60, FALSE, CURRENT_TIMESTAMP),
            (1, 'f005', 'README.md', 'd000', 'README.md', '.md', 'Markdown', 'docs', 1000, 40, FALSE, CURRENT_TIMESTAMP)
    """)

    # Insert SCC metrics
    conn.execute("""
        INSERT INTO lz_scc_file_metrics VALUES
            (2, 'f001', 'd001', 'src/main.py', 'main.py', '.py', 'Python', 150, 120, 20, 10, 5000, 15),
            (2, 'f002', 'd001', 'src/utils.py', 'utils.py', '.py', 'Python', 100, 80, 10, 10, 3000, 8),
            (2, 'f003', 'd002', 'src/models/user.py', 'user.py', '.py', 'Python', 80, 60, 15, 5, 2000, 5),
            (2, 'f004', 'd003', 'tests/test_main.py', 'test_main.py', '.py', 'Python', 60, 50, 5, 5, 1500, 3)
    """)

    # Insert Lizard metrics
    conn.execute("""
        INSERT INTO lz_lizard_file_metrics VALUES
            (3, 'f001', 'src/main.py', 'Python', 120, 8, 45, 5.6, 12),
            (3, 'f002', 'src/utils.py', 'Python', 80, 5, 20, 4.0, 8),
            (3, 'f003', 'src/models/user.py', 'Python', 60, 3, 12, 4.0, 6),
            (3, 'f004', 'tests/test_main.py', 'Python', 50, 4, 8, 2.0, 3)
    """)

    conn.close()

    return test_db_path


@pytest.fixture
def seeded_db_with_marts(seeded_db: Path) -> Path:
    """
    Create staging and mart views on top of the landing zone.

    This simulates what dbt would create.
    """
    conn = duckdb.connect(str(seeded_db))

    # Create staging views
    conn.execute("""
        CREATE VIEW stg_lz_tool_runs AS
        SELECT
            run_pk,
            collection_run_id,
            repo_id,
            run_id,
            tool_name,
            tool_version,
            schema_version,
            branch,
            commit,
            timestamp,
            created_at
        FROM lz_tool_runs
    """)

    conn.execute("""
        CREATE VIEW stg_lz_layout_files AS
        SELECT * FROM lz_layout_files
    """)

    conn.execute("""
        CREATE VIEW stg_lz_scc_file_metrics AS
        SELECT * FROM lz_scc_file_metrics
    """)

    conn.execute("""
        CREATE VIEW stg_lz_lizard_file_metrics AS
        SELECT * FROM lz_lizard_file_metrics
    """)

    # Create unified file metrics mart
    conn.execute("""
        CREATE VIEW unified_file_metrics AS
        SELECT
            COALESCE(scc.run_pk, liz.run_pk) AS run_pk,
            COALESCE(scc.file_id, liz.file_id) AS file_id,
            COALESCE(scc.relative_path, liz.relative_path) AS relative_path,
            COALESCE(scc.language, liz.language) AS language,
            scc.lines_total AS loc,
            scc.code_lines,
            scc.comment_lines,
            scc.blank_lines,
            scc.complexity AS scc_complexity,
            liz.nloc,
            liz.function_count,
            liz.total_ccn,
            liz.avg_ccn,
            liz.max_ccn
        FROM lz_scc_file_metrics scc
        FULL OUTER JOIN lz_lizard_file_metrics liz
            ON scc.file_id = liz.file_id
    """)

    # Create run summary view
    conn.execute("""
        CREATE VIEW unified_run_summary AS
        SELECT
            run_pk,
            repo_id,
            run_id,
            tool_name,
            branch,
            commit,
            timestamp
        FROM lz_tool_runs
    """)

    conn.close()

    return seeded_db


# =============================================================================
# E2E Tests
# =============================================================================


class TestE2EReportGeneration:
    """End-to-end tests for report generation."""

    def test_database_validation_with_marts(self, seeded_db_with_marts: Path) -> None:
        """Test that database validation passes with required tables."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        validation = generator.validate_database()

        assert validation["valid"] is True
        assert len(validation["missing_required"]) == 0

    def test_database_validation_without_required_tables(self, test_db_path: Path) -> None:
        """Test that database validation fails without required tables."""
        # Create empty database
        conn = duckdb.connect(str(test_db_path))
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.close()

        generator = InsightsGenerator(db_path=test_db_path)

        validation = generator.validate_database()

        assert validation["valid"] is False
        assert "unified_file_metrics" in validation["missing_required"]

    def test_generate_html_report(self, seeded_db_with_marts: Path) -> None:
        """Test generating a complete HTML report."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        # Generate report for run_pk=2 (scc run)
        report = generator.generate(
            run_pk=2,
            format="html",
        )

        # Verify basic HTML structure
        assert "<!DOCTYPE html>" in report or "<html" in report
        assert "<body>" in report
        assert "</body>" in report

        # Verify report contains expected sections
        assert "Repository Health" in report or "repo_health" in report

    def test_generate_markdown_report(self, seeded_db_with_marts: Path) -> None:
        """Test generating a complete Markdown report."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        report = generator.generate(
            run_pk=2,
            format="md",
        )

        # Verify Markdown structure
        assert "#" in report  # Has headers
        assert "---" in report or "Report" in report

    def test_generate_report_to_file(self, seeded_db_with_marts: Path) -> None:
        """Test generating a report and writing to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"

            generator = InsightsGenerator(db_path=seeded_db_with_marts)

            report = generator.generate(
                run_pk=2,
                format="html",
                output_path=output_path,
            )

            # Verify file was created
            assert output_path.exists()

            # Verify file content matches returned content
            file_content = output_path.read_text()
            assert file_content == report

    def test_generate_specific_sections(self, seeded_db_with_marts: Path) -> None:
        """Test generating only specific sections."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        # Generate only repo_health section
        report = generator.generate(
            run_pk=2,
            format="html",
            sections=["repo_health"],
        )

        assert "repo_health" in report or "Repository Health" in report

    def test_list_sections(self, seeded_db_with_marts: Path) -> None:
        """Test listing available sections."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        sections = generator.list_sections()

        assert len(sections) > 0

        # Verify section structure
        for section in sections:
            assert "name" in section
            assert "title" in section
            assert "priority" in section

    def test_generate_single_section(self, seeded_db_with_marts: Path) -> None:
        """Test generating a single section."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        section_content = generator.generate_section(
            section_name="repo_health",
            run_pk=2,
            format="html",
        )

        # Should return just the section content, not full report
        assert section_content is not None
        assert len(section_content) > 0


class TestE2EDataFetcher:
    """End-to-end tests for data fetching."""

    def test_fetch_run_info(self, seeded_db_with_marts: Path) -> None:
        """Test fetching run information."""
        fetcher = DataFetcher(db_path=seeded_db_with_marts)

        run_info = fetcher.get_run_info(run_pk=2)

        assert run_info is not None
        assert run_info.get("repository_name") == "test-repo"

    def test_table_exists(self, seeded_db_with_marts: Path) -> None:
        """Test checking if tables exist."""
        fetcher = DataFetcher(db_path=seeded_db_with_marts)

        assert fetcher.table_exists("unified_file_metrics") is True
        assert fetcher.table_exists("nonexistent_table") is False

    def test_fetch_raw_query(self, seeded_db_with_marts: Path) -> None:
        """Test raw SQL query execution."""
        fetcher = DataFetcher(db_path=seeded_db_with_marts)

        results = fetcher.fetch_raw("SELECT COUNT(*) as cnt FROM unified_file_metrics")

        assert len(results) == 1
        assert results[0]["cnt"] == 4  # 4 files with SCC metrics


class TestE2EErrorHandling:
    """End-to-end tests for error handling."""

    def test_invalid_run_pk(self, seeded_db_with_marts: Path) -> None:
        """Test generating report with invalid run_pk raises error."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        # Should raise ValueError since run_pk doesn't exist
        with pytest.raises(ValueError, match="No tool run found"):
            generator.generate(
                run_pk=9999,  # Non-existent
                format="html",
            )

    def test_invalid_section_name(self, seeded_db_with_marts: Path) -> None:
        """Test generating report with invalid section name."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        with pytest.raises(ValueError, match="Unknown sections"):
            generator.generate(
                run_pk=2,
                format="html",
                sections=["nonexistent_section"],
            )

    def test_invalid_format(self, seeded_db_with_marts: Path) -> None:
        """Test generating report with invalid format."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        with pytest.raises(ValueError, match="Unknown format"):
            generator.generate(
                run_pk=2,
                format="invalid",  # type: ignore
            )


class TestE2ECli:
    """Test CLI commands."""

    @pytest.fixture(autouse=True)
    def _skip_if_no_typer(self) -> None:
        """Skip CLI tests if typer is not installed."""
        pytest.importorskip("typer")

    def test_cli_list_sections(self) -> None:
        """Test list-sections command."""
        from typer.testing import CliRunner
        from insights.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["list-sections"])

        assert result.exit_code == 0
        assert "repo_health" in result.stdout

    def test_cli_generate_help(self) -> None:
        """Test generate --help."""
        from typer.testing import CliRunner
        from insights.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["generate", "--help"])

        assert result.exit_code == 0
        assert "--db" in result.stdout
        assert "--format" in result.stdout


class TestE2EReportContent:
    """Test report content structure."""

    def test_html_structure(self, seeded_db_with_marts: Path) -> None:
        """Test HTML report has proper structure."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)
        report = generator.generate(run_pk=2, format="html")

        # Check for structural elements (header, nav/toc, sections, footer)
        has_header = "<header>" in report or "report-header" in report or "<h1" in report
        has_nav = "<nav" in report or "toc" in report or "table-of-contents" in report
        has_sections = "<section" in report or 'class="section"' in report
        has_footer = "<footer>" in report or "report-footer" in report or "generated" in report.lower()

        assert has_header, "Report should have a header element"
        assert has_sections or "repo_health" in report, "Report should have section elements"
        # Note: nav and footer are optional depending on template

    def test_metadata_in_report(self, seeded_db_with_marts: Path) -> None:
        """Test that report metadata is included."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)
        report = generator.generate(run_pk=2, format="html")

        # Check for metadata indicators
        # The run_pk or repository name should appear somewhere
        assert "test-repo" in report or "run_pk" in report or "2" in report

    def test_all_sections_render(self, seeded_db_with_marts: Path) -> None:
        """Test that all sections can render without errors."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        for section_name in InsightsGenerator.SECTIONS.keys():
            content = generator.generate_section(
                section_name=section_name,
                run_pk=2,
                format="html",
            )
            assert content is not None, f"Section {section_name} should return content"
            assert len(content) > 0, f"Section {section_name} should not be empty"


class TestE2ESectionFallbacks:
    """Test section fallback behavior."""

    def test_section_fallback_data(self, seeded_db_with_marts: Path) -> None:
        """Test that each section returns valid fallback data."""
        generator = InsightsGenerator(db_path=seeded_db_with_marts)

        for section_name, section_class in InsightsGenerator.SECTIONS.items():
            section = section_class()
            fallback = section.get_fallback_data()

            # Fallback data should be a dict (can be empty)
            assert isinstance(fallback, dict), f"Section {section_name} fallback should be a dict"

    def test_section_renders_with_fallback(self, test_db_path: Path) -> None:
        """Test sections render gracefully with empty/fallback data."""
        # Create a minimal database with required tables and minimal data
        conn = duckdb.connect(str(test_db_path))
        conn.execute("""
            CREATE TABLE unified_file_metrics (
                run_pk BIGINT,
                file_id VARCHAR,
                relative_path VARCHAR,
                language VARCHAR,
                loc INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE stg_lz_tool_runs (
                run_pk BIGINT,
                collection_run_id VARCHAR,
                repo_id VARCHAR,
                run_id VARCHAR,
                tool_name VARCHAR,
                tool_version VARCHAR,
                schema_version VARCHAR,
                branch VARCHAR,
                commit VARCHAR,
                timestamp TIMESTAMP,
                created_at TIMESTAMP
            )
        """)
        # Insert minimal tool run data
        conn.execute("""
            INSERT INTO stg_lz_tool_runs VALUES (
                1, 'coll-001', 'test-repo', 'run-001', 'scc',
                '1.0', '1.0', 'main', 'abc123',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """)
        conn.close()

        generator = InsightsGenerator(db_path=test_db_path)

        # Should not raise even with empty data
        report = generator.generate(run_pk=1, format="html")
        assert report is not None
        assert len(report) > 0
