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
    PRIMARY KEY (collection_run_id),
    UNIQUE (repo_id, commit)
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
    PRIMARY KEY (run_pk),
    UNIQUE (collection_run_id, tool_name)
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

CREATE TABLE lz_layout_directories (
    run_pk BIGINT NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    parent_id VARCHAR,
    depth INTEGER NOT NULL,
    file_count INTEGER,
    total_size_bytes BIGINT,
    PRIMARY KEY (run_pk, directory_id)
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
    uloc INTEGER,
    comment_ratio DOUBLE,
    blank_ratio DOUBLE,
    code_ratio DOUBLE,
    complexity_density DOUBLE,
    dryness DOUBLE,
    bytes_per_loc DOUBLE,
    is_minified BOOLEAN,
    is_generated BOOLEAN,
    is_binary BOOLEAN,
    classification VARCHAR,
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

CREATE TABLE lz_lizard_function_metrics (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    function_name VARCHAR NOT NULL,
    long_name VARCHAR,
    ccn INTEGER,
    nloc INTEGER,
    params INTEGER,
    token_count INTEGER,
    line_start INTEGER,
    line_end INTEGER,
    PRIMARY KEY (run_pk, file_id, function_name, line_start)
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
    column_start INTEGER,
    column_end INTEGER,
    message TEXT,
    code_snippet TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id, rule_id, line_start)
);

CREATE TABLE lz_gitleaks_secrets (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR,
    relative_path VARCHAR NOT NULL,
    rule_id VARCHAR NOT NULL,
    secret_type VARCHAR,
    severity VARCHAR,
    line_number INTEGER,
    commit_hash VARCHAR,
    commit_author VARCHAR,
    commit_date VARCHAR,
    fingerprint VARCHAR,
    in_current_head BOOLEAN,
    entropy DOUBLE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id, rule_id, line_number, fingerprint)
);

CREATE TABLE lz_roslyn_violations (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    rule_id VARCHAR NOT NULL,
    dd_category VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    message TEXT,
    line_start INTEGER,
    line_end INTEGER,
    column_start INTEGER,
    column_end INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id, rule_id, line_start, column_start)
);

CREATE TABLE lz_devskim_findings (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    rule_id VARCHAR NOT NULL,
    dd_category VARCHAR,
    severity VARCHAR,
    line_start INTEGER,
    line_end INTEGER,
    column_start INTEGER,
    column_end INTEGER,
    message TEXT,
    code_snippet TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id, rule_id, line_start)
);

CREATE TABLE lz_sonarqube_issues (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    issue_key VARCHAR NOT NULL,
    rule_id VARCHAR NOT NULL,
    issue_type VARCHAR,
    severity VARCHAR,
    message TEXT,
    line_start INTEGER,
    line_end INTEGER,
    effort VARCHAR,
    status VARCHAR,
    tags VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id, issue_key)
);

CREATE TABLE lz_sonarqube_metrics (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    ncloc INTEGER,
    complexity INTEGER,
    cognitive_complexity INTEGER,
    duplicated_lines INTEGER,
    duplicated_lines_density DOUBLE,
    code_smells INTEGER,
    bugs INTEGER,
    vulnerabilities INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id)
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
    published_date VARCHAR,
    age_days INTEGER,
    fix_available BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, target_key, vulnerability_id, package_name)
);

CREATE TABLE lz_trivy_targets (
    run_pk BIGINT NOT NULL,
    target_key VARCHAR NOT NULL,
    file_id VARCHAR,
    directory_id VARCHAR,
    relative_path VARCHAR NOT NULL,
    target_type VARCHAR,
    vulnerability_count INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, target_key)
);

CREATE TABLE lz_trivy_iac_misconfigs (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR,
    directory_id VARCHAR,
    relative_path VARCHAR NOT NULL,
    misconfig_id VARCHAR NOT NULL,
    severity VARCHAR,
    title VARCHAR,
    description TEXT,
    resolution TEXT,
    target_type VARCHAR,
    start_line INTEGER,
    end_line INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, relative_path, misconfig_id, start_line)
);

-- =============================================================================
-- git-sizer: Repository health metrics
-- =============================================================================

CREATE TABLE lz_git_sizer_metrics (
    run_pk BIGINT NOT NULL PRIMARY KEY,
    repo_id VARCHAR NOT NULL,
    health_grade VARCHAR NOT NULL,
    duration_ms INTEGER,
    -- Commit metrics
    commit_count INTEGER,
    commit_total_size BIGINT,
    max_commit_size BIGINT,
    max_history_depth INTEGER,
    max_parent_count INTEGER,
    -- Tree metrics
    tree_count INTEGER,
    tree_total_size BIGINT,
    tree_total_entries INTEGER,
    max_tree_entries INTEGER,
    -- Blob metrics
    blob_count INTEGER,
    blob_total_size BIGINT,
    max_blob_size BIGINT,
    -- Tag metrics
    tag_count INTEGER,
    max_tag_depth INTEGER,
    -- Reference metrics
    reference_count INTEGER,
    branch_count INTEGER,
    -- Path metrics
    max_path_depth INTEGER,
    max_path_length INTEGER,
    -- Expanded checkout metrics
    expanded_tree_count INTEGER,
    expanded_blob_count INTEGER,
    expanded_blob_size BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lz_git_sizer_violations (
    run_pk BIGINT NOT NULL,
    metric VARCHAR NOT NULL,
    value_display VARCHAR,
    raw_value BIGINT,
    level INTEGER NOT NULL,
    object_ref VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, metric)
);

CREATE TABLE lz_git_sizer_lfs_candidates (
    run_pk BIGINT NOT NULL,
    file_path VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_path)
);

-- =============================================================================
-- symbol-scanner: Code symbol extraction
-- =============================================================================

CREATE TABLE lz_code_symbols (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    symbol_name VARCHAR NOT NULL,
    symbol_type VARCHAR NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    is_exported BOOLEAN DEFAULT FALSE,
    parameters INTEGER,
    parent_symbol VARCHAR,
    docstring TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id, symbol_name, line_start)
);

CREATE TABLE lz_symbol_calls (
    run_pk BIGINT NOT NULL,
    caller_file_id VARCHAR NOT NULL,
    caller_directory_id VARCHAR NOT NULL,
    caller_file_path VARCHAR NOT NULL,
    caller_symbol VARCHAR NOT NULL,
    callee_symbol VARCHAR NOT NULL,
    callee_file_id VARCHAR,
    callee_file_path VARCHAR,
    line_number INTEGER,
    call_type VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, caller_file_id, caller_symbol, callee_symbol, line_number)
);

CREATE TABLE lz_file_imports (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    imported_path VARCHAR NOT NULL,
    imported_symbols VARCHAR,
    import_type VARCHAR,
    line_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id, imported_path, line_number)
);

-- =============================================================================
-- scancode: License analysis
-- =============================================================================

CREATE TABLE lz_scancode_file_licenses (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    spdx_id VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    confidence DOUBLE NOT NULL,
    match_type VARCHAR NOT NULL,
    line_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id, spdx_id, line_number)
);

CREATE TABLE lz_scancode_summary (
    run_pk BIGINT NOT NULL PRIMARY KEY,
    total_files_scanned INTEGER NOT NULL,
    files_with_licenses INTEGER NOT NULL,
    overall_risk VARCHAR NOT NULL,
    has_permissive BOOLEAN NOT NULL,
    has_weak_copyleft BOOLEAN NOT NULL,
    has_copyleft BOOLEAN NOT NULL,
    has_unknown BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- pmd-cpd: Code duplication detection
-- =============================================================================

CREATE TABLE lz_pmd_cpd_file_metrics (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    language VARCHAR,
    total_lines INTEGER NOT NULL,
    duplicate_lines INTEGER NOT NULL,
    duplicate_blocks INTEGER NOT NULL,
    duplication_percentage DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id)
);

CREATE TABLE lz_pmd_cpd_duplications (
    run_pk BIGINT NOT NULL,
    clone_id VARCHAR NOT NULL,
    lines INTEGER NOT NULL,
    tokens INTEGER NOT NULL,
    occurrence_count INTEGER NOT NULL,
    is_cross_file BOOLEAN NOT NULL,
    code_fragment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, clone_id)
);

CREATE TABLE lz_pmd_cpd_occurrences (
    run_pk BIGINT NOT NULL,
    clone_id VARCHAR NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    column_start INTEGER,
    column_end INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, clone_id, file_id, line_start)
);

-- =============================================================================
-- dotcover: Code coverage metrics
-- =============================================================================

-- Assembly-level summary
CREATE TABLE lz_dotcover_assembly_coverage (
    run_pk BIGINT NOT NULL,
    assembly_name VARCHAR NOT NULL,
    covered_statements INTEGER NOT NULL,
    total_statements INTEGER NOT NULL,
    statement_coverage_pct DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, assembly_name)
);

-- Type (class) level - links to files when available
CREATE TABLE lz_dotcover_type_coverage (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR,            -- NULL if file mapping unavailable
    directory_id VARCHAR,
    relative_path VARCHAR,      -- Source file path
    assembly_name VARCHAR NOT NULL,
    namespace VARCHAR,
    type_name VARCHAR NOT NULL,
    covered_statements INTEGER NOT NULL,
    total_statements INTEGER NOT NULL,
    statement_coverage_pct DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, assembly_name, type_name)
);

-- Method-level detail
CREATE TABLE lz_dotcover_method_coverage (
    run_pk BIGINT NOT NULL,
    assembly_name VARCHAR NOT NULL,
    type_name VARCHAR NOT NULL,
    method_name VARCHAR NOT NULL,
    covered_statements INTEGER NOT NULL,
    total_statements INTEGER NOT NULL,
    statement_coverage_pct DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, assembly_name, type_name, method_name)
);

-- =============================================================================
-- dependensee: .NET dependency analysis
-- =============================================================================

CREATE TABLE lz_dependensee_projects (
    run_pk BIGINT NOT NULL,
    project_path VARCHAR NOT NULL,
    project_name VARCHAR NOT NULL,
    target_framework VARCHAR,
    project_reference_count INTEGER NOT NULL,
    package_reference_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, project_path)
);

CREATE TABLE lz_dependensee_project_refs (
    run_pk BIGINT NOT NULL,
    source_project_path VARCHAR NOT NULL,
    target_project_path VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, source_project_path, target_project_path)
);

CREATE TABLE lz_dependensee_package_refs (
    run_pk BIGINT NOT NULL,
    project_path VARCHAR NOT NULL,
    package_name VARCHAR NOT NULL,
    package_version VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, project_path, package_name)
);

-- =============================================================================
-- git-fame: Author-level authorship metrics
-- =============================================================================

CREATE TABLE lz_git_fame_authors (
    run_pk BIGINT NOT NULL,
    author_name VARCHAR NOT NULL,
    author_email VARCHAR,
    surviving_loc INTEGER NOT NULL,
    ownership_pct DOUBLE NOT NULL,
    insertions_total INTEGER NOT NULL,
    deletions_total INTEGER NOT NULL,
    commit_count INTEGER NOT NULL,
    files_touched INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, author_name)
);

CREATE TABLE lz_git_fame_summary (
    run_pk BIGINT NOT NULL PRIMARY KEY,
    repo_id VARCHAR NOT NULL,
    author_count INTEGER NOT NULL,
    total_loc INTEGER NOT NULL,
    hhi_index DOUBLE NOT NULL,
    bus_factor INTEGER NOT NULL,
    top_author_pct DOUBLE NOT NULL,
    top_two_pct DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- git-blame-scanner: Per-file authorship metrics
-- =============================================================================

CREATE TABLE lz_git_blame_summary (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    total_lines INTEGER NOT NULL,
    unique_authors INTEGER NOT NULL,
    top_author VARCHAR NOT NULL,
    top_author_lines INTEGER NOT NULL,
    top_author_pct DOUBLE NOT NULL,
    last_modified DATE,
    churn_30d INTEGER NOT NULL,
    churn_90d INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id)
);

CREATE TABLE lz_git_blame_author_stats (
    run_pk BIGINT NOT NULL,
    author_email VARCHAR NOT NULL,
    total_files INTEGER NOT NULL,
    total_lines INTEGER NOT NULL,
    exclusive_files INTEGER NOT NULL,
    avg_ownership_pct DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, author_email)
);
