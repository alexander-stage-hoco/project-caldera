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

# Install insights package (editable)
RUN .venv/bin/pip install --no-cache-dir -e src/insights/

ENV PATH="/caldera/.venv/bin:${PATH}" \
    PYTHONPATH="/caldera/src"

ENTRYPOINT ["python", "scripts/docker_orchestrator_entrypoint.py"]
