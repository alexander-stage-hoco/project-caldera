ARG BASE_IMAGE=caldera-python-base:latest
FROM ${BASE_IMAGE}

COPY src/tools/scancode/ /caldera/src/tools/scancode/
WORKDIR /caldera/src/tools/scancode

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
