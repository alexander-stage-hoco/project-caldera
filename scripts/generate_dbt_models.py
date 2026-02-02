#!/usr/bin/env python3
"""dbt model generator for Project Caldera.

This script generates dbt models for a tool based on its landing zone table structure.
It creates staging models and rollup models following the Caldera patterns.

Usage:
    python scripts/generate_dbt_models.py <tool-name> [options]

Examples:
    # Generate all models for a tool
    python scripts/generate_dbt_models.py my-tool --table lz_my_tool_metrics \
        --metrics lines,complexity,coverage

    # Dry run to see what would be generated
    python scripts/generate_dbt_models.py my-tool --table lz_my_tool_metrics \
        --metrics lines,complexity --dry-run

    # Generate only staging model
    python scripts/generate_dbt_models.py my-tool --table lz_my_tool_metrics \
        --staging-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


def normalize_tool_name(tool_name: str) -> str:
    """Normalize tool name for use in dbt model names.

    Examples:
        roslyn-analyzers -> roslyn
        layout-scanner -> layout
        git-sizer -> git_sizer
    """
    name = tool_name.replace("-scanner", "").replace("-analyzers", "")
    return name.replace("-", "_")


def get_staging_model_template(tool_name: str, table_name: str, columns: list[str]) -> str:
    """Generate staging model SQL."""
    normalized = normalize_tool_name(tool_name)
    model_name = f"stg_{table_name}"

    columns_sql = ",\n    ".join(columns) if columns else "-- TODO: Add column list from schema.sql\n    *"

    return f"""-- Staging model for {tool_name}
-- Source: {table_name}

select
    {columns_sql}
from {{{{ source('lz', '{table_name}') }}}}
"""


def get_direct_counts_template(tool_name: str, table_name: str, metrics: list[str]) -> str:
    """Generate direct rollup counts model SQL."""
    normalized = normalize_tool_name(tool_name)

    # Build aggregation columns
    agg_columns = []
    for metric in metrics:
        agg_columns.append(f"sum({metric}) as total_{metric}")
    agg_columns_sql = ",\n        ".join(agg_columns)

    select_columns = ",\n    ".join([f"a.total_{m}" for m in metrics])

    return f"""-- {tool_name.upper()} file counts per directory (direct - only files in that directory)

with {normalized}_runs as (
    select run_pk, collection_run_id
    from {{{{ source('lz', 'lz_tool_runs') }}}}
    where tool_name = '{tool_name}'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{{{ source('lz', 'lz_tool_runs') }}}}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        tr.run_pk as {normalized}_run_pk,
        lr.run_pk as layout_run_pk,
        tr.collection_run_id
    from {normalized}_runs tr
    join layout_runs lr
        on lr.collection_run_id = tr.collection_run_id
),
dir_files as (
    select
        rm.{normalized}_run_pk as run_pk,
        rm.layout_run_pk,
        sm.directory_id,
        sm.file_id,
        {', '.join([f'sm.{m}' for m in metrics])}
    from {{{{ ref('stg_{table_name}') }}}} sm
    join run_map rm
        on rm.{normalized}_run_pk = sm.run_pk
),
directory_paths as (
    select
        run_pk,
        directory_id,
        relative_path
    from {{{{ source('lz', 'lz_layout_directories') }}}}
),
aggregated as (
    select
        run_pk,
        layout_run_pk,
        directory_id,
        count(distinct file_id) as file_count,
        {agg_columns_sql}
    from dir_files
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.file_count,
    {select_columns}
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
"""


def get_recursive_counts_template(tool_name: str, table_name: str, metrics: list[str]) -> str:
    """Generate recursive rollup counts model SQL."""
    normalized = normalize_tool_name(tool_name)

    # Build aggregation columns
    agg_columns = []
    for metric in metrics:
        agg_columns.append(f"sum({metric}) as total_{metric}")
    agg_columns_sql = ",\n        ".join(agg_columns)

    select_columns = ",\n    ".join([f"a.total_{m}" for m in metrics])

    return f"""-- {tool_name.upper()} file counts per directory (recursive - all files in subtree)

with recursive {normalized}_runs as (
    select run_pk, collection_run_id
    from {{{{ source('lz', 'lz_tool_runs') }}}}
    where tool_name = '{tool_name}'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{{{ source('lz', 'lz_tool_runs') }}}}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        tr.run_pk as {normalized}_run_pk,
        lr.run_pk as layout_run_pk,
        tr.collection_run_id
    from {normalized}_runs tr
    join layout_runs lr
        on lr.collection_run_id = tr.collection_run_id
),
dir_tree as (
    -- Base case: each directory is its own ancestor
    select
        rm.{normalized}_run_pk,
        rm.layout_run_pk,
        ld.directory_id as ancestor_id,
        ld.directory_id as descendant_id
    from {{{{ source('lz', 'lz_layout_directories') }}}} ld
    join run_map rm
        on rm.layout_run_pk = ld.run_pk

    union all

    -- Recursive case: parent inherits children
    select
        parent.{normalized}_run_pk,
        parent.layout_run_pk,
        parent.ancestor_id,
        child.directory_id as descendant_id
    from dir_tree parent
    join {{{{ source('lz', 'lz_layout_directories') }}}} child
        on child.run_pk = parent.layout_run_pk
        and child.parent_id = parent.descendant_id
),
files_with_ancestor as (
    select
        dt.{normalized}_run_pk,
        dt.layout_run_pk,
        dt.ancestor_id as directory_id,
        sm.file_id,
        {', '.join([f'sm.{m}' for m in metrics])}
    from {{{{ ref('stg_{table_name}') }}}} sm
    join dir_tree dt
        on dt.{normalized}_run_pk = sm.run_pk
        and dt.descendant_id = sm.directory_id
),
directory_paths as (
    select
        run_pk,
        directory_id,
        relative_path
    from {{{{ source('lz', 'lz_layout_directories') }}}}
),
aggregated as (
    select
        {normalized}_run_pk as run_pk,
        layout_run_pk,
        directory_id,
        count(distinct file_id) as file_count,
        {agg_columns_sql}
    from files_with_ancestor
    group by {normalized}_run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.file_count,
    {select_columns}
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
"""


def get_distribution_model_template(tool_name: str, table_name: str, metrics: list[str], scope: str) -> str:
    """Generate distribution model using the macro.

    Args:
        tool_name: Tool name
        table_name: Landing zone table name
        metrics: List of metric column names
        scope: 'direct' or 'recursive'
    """
    metrics_list = ", ".join([f"'{m}'" for m in metrics])
    return f"""{{{{ calculate_distribution_stats(
    tool_name='{tool_name}',
    scope='{scope}',
    metrics_table='{table_name}',
    metrics=[{metrics_list}]
) }}}}
"""


def get_schema_yml_snippet(tool_name: str, table_name: str, models: list[str]) -> str:
    """Generate schema.yml snippet for the models."""
    normalized = normalize_tool_name(tool_name)
    lines = []

    for model in models:
        lines.append(f"  - name: {model}")
        lines.append(f"    columns:")
        lines.append(f"      - name: run_pk")
        lines.append(f"        tests:")
        lines.append(f"          - not_null")
        if "stg_" in model:
            lines.append(f"      - name: file_id")
            lines.append(f"        tests:")
            lines.append(f"          - not_null")
            lines.append(f"      - name: relative_path")
            lines.append(f"        tests:")
            lines.append(f"          - not_null")
        elif "rollup_" in model:
            lines.append(f"      - name: directory_id")
            lines.append(f"        tests:")
            lines.append(f"          - not_null")
            lines.append(f"      - name: directory_path")
            lines.append(f"        tests:")
            lines.append(f"          - not_null")

    return "\n".join(lines)


def generate_dbt_models(
    tool_name: str,
    table_name: str,
    metrics: list[str],
    columns: list[str] | None = None,
    staging_only: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Generate dbt models for a tool.

    Args:
        tool_name: Tool name (e.g., 'my-tool')
        table_name: Landing zone table name (e.g., 'lz_my_tool_metrics')
        metrics: List of metric columns for rollups
        columns: List of columns for staging model (defaults to standard set)
        staging_only: Only generate staging model
        dry_run: Print models without writing

    Returns:
        Dictionary with generated model info
    """
    normalized = normalize_tool_name(tool_name)
    dbt_dir = Path("src/sot-engine/dbt/models")
    staging_dir = dbt_dir / "staging"
    marts_dir = dbt_dir / "marts"

    # Default columns if not provided
    if not columns:
        columns = [
            "run_pk",
            "file_id",
            "directory_id",
            "relative_path",
            "filename",
            "-- TODO: Add tool-specific columns",
        ]

    models_created = []

    # Generate staging model
    staging_model = f"stg_{table_name}"
    staging_content = get_staging_model_template(tool_name, table_name, columns)

    if dry_run:
        print(f"=== {staging_model}.sql ===")
        print(staging_content)
        print()
    else:
        staging_dir.mkdir(parents=True, exist_ok=True)
        staging_path = staging_dir / f"{staging_model}.sql"
        staging_path.write_text(staging_content)
        models_created.append(str(staging_path))

    if staging_only:
        return {"models_created": models_created, "staging_model": staging_model}

    # Generate rollup models
    if metrics:
        # Direct counts
        direct_model = f"rollup_{normalized}_directory_counts_direct"
        direct_content = get_direct_counts_template(tool_name, table_name, metrics)
        if dry_run:
            print(f"=== {direct_model}.sql ===")
            print(direct_content)
            print()
        else:
            marts_dir.mkdir(parents=True, exist_ok=True)
            direct_path = marts_dir / f"{direct_model}.sql"
            direct_path.write_text(direct_content)
            models_created.append(str(direct_path))

        # Recursive counts
        recursive_model = f"rollup_{normalized}_directory_counts_recursive"
        recursive_content = get_recursive_counts_template(tool_name, table_name, metrics)
        if dry_run:
            print(f"=== {recursive_model}.sql ===")
            print(recursive_content)
            print()
        else:
            recursive_path = marts_dir / f"{recursive_model}.sql"
            recursive_path.write_text(recursive_content)
            models_created.append(str(recursive_path))

        # Direct distributions
        direct_dist_model = f"rollup_{normalized}_directory_direct_distributions"
        direct_dist_content = get_distribution_model_template(tool_name, table_name, metrics, "direct")
        if dry_run:
            print(f"=== {direct_dist_model}.sql ===")
            print(direct_dist_content)
            print()
        else:
            direct_dist_path = marts_dir / f"{direct_dist_model}.sql"
            direct_dist_path.write_text(direct_dist_content)
            models_created.append(str(direct_dist_path))

        # Recursive distributions
        recursive_dist_model = f"rollup_{normalized}_directory_recursive_distributions"
        recursive_dist_content = get_distribution_model_template(tool_name, table_name, metrics, "recursive")
        if dry_run:
            print(f"=== {recursive_dist_model}.sql ===")
            print(recursive_dist_content)
            print()
        else:
            recursive_dist_path = marts_dir / f"{recursive_dist_model}.sql"
            recursive_dist_path.write_text(recursive_dist_content)
            models_created.append(str(recursive_dist_path))

    # Generate schema.yml snippet
    all_models = [staging_model]
    if metrics:
        all_models.extend([
            f"rollup_{normalized}_directory_counts_direct",
            f"rollup_{normalized}_directory_counts_recursive",
            f"rollup_{normalized}_directory_direct_distributions",
            f"rollup_{normalized}_directory_recursive_distributions",
        ])

    schema_snippet = get_schema_yml_snippet(tool_name, table_name, all_models)
    if dry_run:
        print("=== schema.yml snippet (add to models/schema.yml) ===")
        print(schema_snippet)
        print()
    else:
        print("\nAdd the following to src/sot-engine/dbt/models/schema.yml:")
        print("-" * 60)
        print(schema_snippet)
        print("-" * 60)

    return {
        "models_created": models_created,
        "staging_model": staging_model,
        "rollup_models": all_models[1:] if len(all_models) > 1 else [],
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate dbt models for a Caldera tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("tool_name", help="Tool name (e.g., 'my-tool')")
    parser.add_argument(
        "--table",
        required=True,
        help="Landing zone table name (e.g., 'lz_my_tool_metrics')",
    )
    parser.add_argument(
        "--metrics",
        help="Comma-separated list of metric columns for rollups (e.g., 'lines,complexity')",
    )
    parser.add_argument(
        "--columns",
        help="Comma-separated list of columns for staging model",
    )
    parser.add_argument(
        "--staging-only",
        action="store_true",
        help="Only generate staging model",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated models without writing files",
    )

    args = parser.parse_args()

    metrics = [m.strip() for m in args.metrics.split(",")] if args.metrics else []
    columns = [c.strip() for c in args.columns.split(",")] if args.columns else None

    try:
        result = generate_dbt_models(
            tool_name=args.tool_name,
            table_name=args.table,
            metrics=metrics,
            columns=columns,
            staging_only=args.staging_only,
            dry_run=args.dry_run,
        )

        if not args.dry_run:
            print(f"\nModels created:")
            for model in result["models_created"]:
                print(f"  - {model}")
            print("\nNext steps:")
            print("  1. Review generated SQL models")
            print("  2. Add model entries to schema.yml")
            print("  3. Run: cd src/sot-engine/dbt && dbt run")
            print("  4. Run: cd src/sot-engine/dbt && dbt test")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
