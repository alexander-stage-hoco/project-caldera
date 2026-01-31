from pathlib import Path


def render_report_sql(sql_text: str, run_pk: int, limit_rows: int = 10) -> str:
    rendered = sql_text.replace("{% set run_pk = var('run_pk') %}", "")
    rendered = rendered.replace("{% set limit_rows = var('limit', 10) %}", "")
    rendered = rendered.replace("{{ ref('rollup_scc_directory_recursive_distributions') }}", "rollup_scc_directory_recursive_distributions")
    rendered = rendered.replace("{{ ref('rollup_lizard_directory_recursive_distributions') }}", "rollup_lizard_directory_recursive_distributions")
    rendered = rendered.replace("{{ ref('rollup_roslyn_directory_recursive_distributions') }}", "rollup_roslyn_directory_recursive_distributions")
    rendered = rendered.replace("{{ ref('unified_run_summary') }}", "unified_run_summary")
    rendered = rendered.replace("{{ source('lz', 'lz_layout_directories') }}", "lz_layout_directories")
    rendered = rendered.replace("{{ source('lz', 'lz_tool_runs') }}", "lz_tool_runs")
    rendered = rendered.replace("{{ source('lz', 'lz_collection_runs') }}", "lz_collection_runs")
    rendered = rendered.replace("{{ run_pk }}", str(run_pk))
    rendered = rendered.replace("{{ limit_rows }}", str(limit_rows))
    return rendered


def load_sql(path: str) -> str:
    return Path(path).read_text()
