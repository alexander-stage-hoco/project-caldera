ARG BASE_IMAGE=caldera-python-base:latest
FROM ${BASE_IMAGE}

COPY src/tools/layout-scanner/ /caldera/src/tools/layout-scanner/
WORKDIR /caldera/src/tools/layout-scanner

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
