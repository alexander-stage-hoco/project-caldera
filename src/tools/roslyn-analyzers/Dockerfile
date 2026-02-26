ARG BASE_IMAGE=caldera-dotnet-base:latest
FROM ${BASE_IMAGE}

RUN apt-get update && \
    apt-get install -y --no-install-recommends rsync && \
    rm -rf /var/lib/apt/lists/*

COPY src/tools/roslyn-analyzers/ /caldera/src/tools/roslyn-analyzers/
WORKDIR /caldera/src/tools/roslyn-analyzers

RUN make setup

# dotnet build needs write access to the repo (creates bin/obj dirs).
# The runner mounts the repo read-only, so copy only .NET project/source files
# to a writable location (skip .git/, .venv/, eval-repos/, node_modules/ etc.).
RUN printf '#!/bin/sh\n\
rsync -a --include="*/" \
  --include="*.sln" --include="*.csproj" --include="*.fsproj" --include="*.vbproj" \
  --include="*.cs" --include="*.fs" --include="*.vb" \
  --include="*.props" --include="*.targets" --include="global.json" \
  --include="NuGet.Config" --include="nuget.config" --include="Directory.Build.*" \
  --include="*.razor" --include="*.cshtml" \
  --exclude="*" \
  /repo/ /tmp/repo-rw/\n\
exec make analyze SKIP_SETUP=1 REPO_PATH=/tmp/repo-rw OUTPUT_DIR=/output "$@"\n' > /caldera/docker-entrypoint.sh && \
    chmod +x /caldera/docker-entrypoint.sh

ENTRYPOINT ["/caldera/docker-entrypoint.sh"]
