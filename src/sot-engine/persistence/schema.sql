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
