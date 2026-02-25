ARG BASE_IMAGE=caldera-dotnet-base:latest
FROM ${BASE_IMAGE}

RUN dotnet tool install --global Microsoft.CST.DevSkim.CLI
ENV PATH="$PATH:/root/.dotnet/tools"
ENV DOTNET_ROLL_FORWARD=LatestMajor

COPY src/tools/devskim/ /caldera/src/tools/devskim/
WORKDIR /caldera/src/tools/devskim

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
