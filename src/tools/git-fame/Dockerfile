FROM caldera-python-base:latest

COPY src/tools/git-fame/ /caldera/src/tools/git-fame/
WORKDIR /caldera/src/tools/git-fame

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
