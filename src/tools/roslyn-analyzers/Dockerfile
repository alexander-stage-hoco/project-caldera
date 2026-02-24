ARG BASE_IMAGE=caldera-dotnet-base:latest
FROM ${BASE_IMAGE}

COPY src/tools/roslyn-analyzers/ /caldera/src/tools/roslyn-analyzers/
WORKDIR /caldera/src/tools/roslyn-analyzers

RUN make setup

# dotnet build needs write access to the repo (creates bin/obj dirs).
# The runner mounts the repo read-only, so copy it to a writable location first.
RUN printf '#!/bin/sh\ncp -a /repo /tmp/repo-rw\nexec make analyze SKIP_SETUP=1 REPO_PATH=/tmp/repo-rw "$@"\n' > /caldera/docker-entrypoint.sh && \
    chmod +x /caldera/docker-entrypoint.sh

ENTRYPOINT ["/caldera/docker-entrypoint.sh"]
CMD ["OUTPUT_DIR=/output"]
