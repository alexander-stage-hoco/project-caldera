FROM caldera-java-base:latest

ARG PMD_VERSION=7.0.0
RUN curl -sL "https://github.com/pmd/pmd/releases/download/pmd_releases%2F${PMD_VERSION}/pmd-dist-${PMD_VERSION}-bin.zip" \
    -o /tmp/pmd.zip && mkdir -p /caldera/.pmd && unzip -o /tmp/pmd.zip -d /caldera/.pmd && rm /tmp/pmd.zip

COPY src/tools/pmd-cpd/ /caldera/src/tools/pmd-cpd/
WORKDIR /caldera/src/tools/pmd-cpd

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output", \
    "PMD_HOME=/caldera/.pmd"]
