FROM python:3.12-slim AS schema-collector

# Copy all tool dirs, then extract only schemas
COPY src/tools/ /tmp/all-tools/
RUN mkdir -p /tool-schemas && \
    for d in /tmp/all-tools/*/schemas; do \
        tool="$(basename "$(dirname "$d")")"; \
        mkdir -p "/tool-schemas/$tool/schemas" && \
        cp -r "$d"/. "/tool-schemas/$tool/schemas/"; \
    done

FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends git make && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /caldera

# Install Python dependencies
COPY requirements.txt /caldera/
RUN python -m venv .venv && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/sot-engine/ /caldera/src/sot-engine/
COPY src/common/ /caldera/src/common/
COPY src/shared/ /caldera/src/shared/
COPY src/insights/ /caldera/src/insights/
COPY scripts/ /caldera/scripts/

# Copy tool schemas (needed by adapters for validation)
COPY --from=schema-collector /tool-schemas/ /caldera/src/tools/

# Install insights package (editable)
RUN .venv/bin/pip install --no-cache-dir -e src/insights/

# Orchestrator defaults to src/sot-engine/.venv-dbt/bin/dbt — symlink to main venv
# Remove any host venv copied in, then create symlink
RUN rm -rf /caldera/src/sot-engine/.venv-dbt && \
    ln -s /caldera/.venv /caldera/src/sot-engine/.venv-dbt

ENV PATH="/caldera/.venv/bin:${PATH}" \
    PYTHONPATH="/caldera/src"

ENTRYPOINT ["python", "scripts/docker_orchestrator_entrypoint.py"]
