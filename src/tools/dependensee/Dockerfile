FROM caldera-python-base:latest

COPY src/tools/dependensee/ /caldera/src/tools/dependensee/
WORKDIR /caldera/src/tools/dependensee

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
