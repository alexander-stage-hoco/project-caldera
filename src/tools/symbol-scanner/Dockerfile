FROM caldera-python-base:latest

COPY src/tools/symbol-scanner/ /caldera/src/tools/symbol-scanner/
WORKDIR /caldera/src/tools/symbol-scanner

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
