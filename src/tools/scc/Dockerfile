FROM caldera-python-base:latest

ARG SCC_VERSION=3.6.0
RUN curl -sL "https://github.com/boyter/scc/releases/download/v${SCC_VERSION}/scc_Linux_x86_64.tar.gz" \
    | tar xz -C /usr/local/bin scc

COPY src/tools/scc/ /caldera/src/tools/scc/
WORKDIR /caldera/src/tools/scc

# Symlink so the Makefile's SCC_BIN=./bin/scc resolves
RUN mkdir -p bin && ln -s /usr/local/bin/scc bin/scc

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
