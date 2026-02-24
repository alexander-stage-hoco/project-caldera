FROM caldera-python-base:latest

COPY src/tools/lizard/ /caldera/src/tools/lizard/
WORKDIR /caldera/src/tools/lizard

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
