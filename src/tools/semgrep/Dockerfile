FROM caldera-python-base:latest

COPY src/tools/semgrep/ /caldera/src/tools/semgrep/
WORKDIR /caldera/src/tools/semgrep

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
