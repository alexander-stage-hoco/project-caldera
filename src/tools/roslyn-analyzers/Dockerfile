FROM caldera-dotnet-base:latest

COPY src/tools/roslyn-analyzers/ /caldera/src/tools/roslyn-analyzers/
WORKDIR /caldera/src/tools/roslyn-analyzers

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
