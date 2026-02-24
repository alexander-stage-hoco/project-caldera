FROM caldera-python-base:latest

ARG TRIVY_VERSION=0.58.0
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin v${TRIVY_VERSION}

COPY src/tools/trivy/ /caldera/src/tools/trivy/
WORKDIR /caldera/src/tools/trivy

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
