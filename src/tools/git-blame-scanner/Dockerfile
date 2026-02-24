FROM caldera-python-base:latest

COPY src/tools/git-blame-scanner/ /caldera/src/tools/git-blame-scanner/
WORKDIR /caldera/src/tools/git-blame-scanner

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
