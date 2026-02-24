ARG BASE_IMAGE=caldera-python-base:latest
FROM ${BASE_IMAGE}

ARG TRIVY_VERSION=0.58.0
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin v${TRIVY_VERSION}

# Pre-cache vulnerability DB so scans don't need network access
RUN trivy filesystem --download-db-only --cache-dir /root/.cache/trivy 2>/dev/null || true

COPY src/tools/trivy/ /caldera/src/tools/trivy/
WORKDIR /caldera/src/tools/trivy

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
