ARG BASE_IMAGE=caldera-python-base:latest
FROM ${BASE_IMAGE}

ARG GITLEAKS_VERSION=8.18.4
RUN curl -sL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
    | tar xz -C /usr/local/bin gitleaks

COPY src/tools/gitleaks/ /caldera/src/tools/gitleaks/
WORKDIR /caldera/src/tools/gitleaks

# Symlink so the Makefile's bin/gitleaks resolves
RUN mkdir -p bin && ln -sf /usr/local/bin/gitleaks bin/gitleaks

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
