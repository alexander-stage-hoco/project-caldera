ARG BASE_IMAGE=caldera-dotnet-base:latest
FROM ${BASE_IMAGE}

COPY src/tools/dotcover/ /caldera/src/tools/dotcover/
WORKDIR /caldera/src/tools/dotcover

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
