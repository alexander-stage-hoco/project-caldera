FROM caldera-python-base:latest

COPY src/tools/coverage-ingest/ /caldera/src/tools/coverage-ingest/
WORKDIR /caldera/src/tools/coverage-ingest

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
