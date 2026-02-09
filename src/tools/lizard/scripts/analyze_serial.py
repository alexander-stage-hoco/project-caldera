#!/usr/bin/env python3
"""Serial file-by-file lizard analysis to work around multiprocessing hang."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import lizard

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from shared.path_utils import normalize_file_path, normalize_dir_path


def timeout_handler(signum, frame):
    raise TimeoutError("File analysis timed out")


def detect_language(filepath: str) -> str:
    """Detect language from file extension."""
    ext_map = {
        '.cs': 'C#', '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
        '.java': 'Java', '.c': 'C', '.cpp': 'C++', '.h': 'C/C++ Header',
        '.go': 'Go', '.rb': 'Ruby', '.php': 'PHP', '.swift': 'Swift',
        '.kt': 'Kotlin', '.rs': 'Rust', '.scala': 'Scala',
    }
    ext = Path(filepath).suffix.lower()
    return ext_map.get(ext, 'Unknown')


def main():
    parser = argparse.ArgumentParser(description="Serial lizard analysis")
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--repo-name", default="")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--commit", required=True)
    parser.add_argument("--max-file-size", type=int, default=100, help="Max file size in KB")
    parser.add_argument("--timeout", type=int, default=10, help="Per-file timeout in seconds")
    parser.add_argument("-l", "--languages", nargs="+", help="Languages to analyze")
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    repo_name = args.repo_name or repo_path.name
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Lizard version: {lizard.version}")
    print(f"\nAnalyzing {repo_name}...")

    # Directories to exclude
    exclude_dirs = {
        'node_modules', 'vendor', '__pycache__', 'bin', 'obj',
        '.git', '.vs', '.idea', 'packages', 'TestResults',
        'wwwroot', 'dist', 'build', 'coverage', 'artifacts',
        'test', 'tests', 'Test', 'Tests', 'UnitTests',
        'IntegrationTests', 'Benchmarks', '__tests__', 'spec', 'specs',
    }

    # Language filter
    lang_filter = None
    if args.languages:
        lang_filter = {lang.lower() for lang in args.languages}

    # Collect files
    max_size_bytes = args.max_file_size * 1024
    source_files = []
    skipped_large = 0
    skipped_lang = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in exclude_dirs]
        for f in files:
            filepath = Path(root) / f
            lang = detect_language(str(filepath))
            if lang == 'Unknown':
                continue
            if lang_filter and lang.lower() not in lang_filter:
                skipped_lang += 1
                continue
            try:
                if filepath.stat().st_size > max_size_bytes:
                    skipped_large += 1
                    continue
            except OSError:
                continue
            source_files.append(str(filepath))

    if skipped_large > 0:
        print(f"  Skipped {skipped_large} files larger than {args.max_file_size}KB")
    if skipped_lang > 0:
        print(f"  Skipped {skipped_lang} files (language filter)")

    print(f"  Analyzing {len(source_files)} files serially...")

    # Set up signal handler for timeout
    signal.signal(signal.SIGALRM, timeout_handler)

    # Analyze files one at a time
    files_data = []
    functions_data = []
    by_language = defaultdict(lambda: {'files': 0, 'functions': 0, 'nloc': 0, 'ccn': 0})
    skipped_timeout = 0
    skipped_error = 0

    for i, filepath in enumerate(source_files):
        if (i + 1) % 100 == 0:
            print(f"    Progress: {i + 1}/{len(source_files)}")

        signal.alarm(args.timeout)
        try:
            results = list(lizard.analyze([filepath], threads=1))
            signal.alarm(0)

            for file_analysis in results:
                lang = detect_language(file_analysis.filename)
                rel_path = normalize_file_path(file_analysis.filename, repo_path)

                file_ccn = 0
                file_nloc = file_analysis.nloc
                file_functions = []

                for func in file_analysis.function_list:
                    func_data = {
                        'name': func.name,
                        'long_name': func.long_name,
                        'start_line': func.start_line,
                        'end_line': func.end_line,
                        'nloc': func.nloc,
                        'ccn': func.cyclomatic_complexity,
                        'token_count': func.token_count,
                        'parameters': func.parameter_count,
                    }
                    file_functions.append(func_data)
                    functions_data.append({
                        'file_path': rel_path,
                        'language': lang,
                        **func_data
                    })
                    file_ccn += func.cyclomatic_complexity

                files_data.append({
                    'path': rel_path,
                    'language': lang,
                    'nloc': file_nloc,
                    'ccn': file_ccn,
                    'functions': file_functions,
                    'function_count': len(file_functions),
                })

                by_language[lang]['files'] += 1
                by_language[lang]['functions'] += len(file_functions)
                by_language[lang]['nloc'] += file_nloc
                by_language[lang]['ccn'] += file_ccn

        except TimeoutError:
            skipped_timeout += 1
            signal.alarm(0)
        except Exception as e:
            skipped_error += 1
            signal.alarm(0)

    if skipped_timeout > 0:
        print(f"  Skipped {skipped_timeout} files (timeout)")
    if skipped_error > 0:
        print(f"  Skipped {skipped_error} files (errors)")

    # Calculate summary
    total_files = len(files_data)
    total_functions = len(functions_data)
    total_ccn = sum(f['ccn'] for f in functions_data) if functions_data else 0
    avg_ccn = total_ccn / total_functions if total_functions > 0 else 0
    max_ccn = max((f['ccn'] for f in functions_data), default=0)
    functions_over = sum(1 for f in functions_data if f['ccn'] > 15)

    # Build output
    timestamp = datetime.now(timezone.utc).isoformat()
    output = {
        'tool_name': 'lizard',
        'tool_version': lizard.version,
        'generated_at': timestamp,
        'repo_name': repo_name,
        'repo_path': str(repo_path),
        'repo_id': args.repo_id,
        'branch': args.branch,
        'commit': args.commit,
        'run_id': args.run_id,
        'timestamp': timestamp,
        'root_path': '.',
        'summary': {
            'total_files': total_files,
            'total_functions': total_functions,
            'total_ccn': total_ccn,
            'avg_ccn': round(avg_ccn, 2),
            'max_ccn': max_ccn,
            'functions_over_threshold': functions_over,
        },
        'files': files_data,
        'functions': functions_data,
        'by_language': dict(by_language),
        'directories': [],  # Skipping directory aggregation for now
    }

    output_path = output_dir / 'output.json'
    output_path.write_text(json.dumps(output, indent=2))

    print(f"\nFiles analyzed: {total_files}")
    print(f"Functions found: {total_functions}")
    print(f"Total CCN: {total_ccn}")
    print(f"Avg CCN: {avg_ccn:.2f}")
    print(f"Max CCN: {max_ccn}")
    print(f"Functions over threshold: {functions_over}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
