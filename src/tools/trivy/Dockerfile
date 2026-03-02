ARG BASE_IMAGE=caldera-python-base:latest
FROM ${BASE_IMAGE}

RUN apt-get update && \
    apt-get install -y wget apt-transport-https gnupg && \
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor > /usr/share/keyrings/trivy.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" > /etc/apt/sources.list.d/trivy.list && \
    apt-get update && \
    apt-get install -y trivy && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Pre-cache vulnerability DB so scans don't need network access
RUN trivy filesystem --download-db-only --cache-dir /root/.cache/trivy || true
RUN trivy filesystem --download-java-db-only --cache-dir /root/.cache/trivy || true

COPY src/tools/trivy/ /caldera/src/tools/trivy/
WORKDIR /caldera/src/tools/trivy

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
