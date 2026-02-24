FROM caldera-python-base:latest

ARG GIT_SIZER_VERSION=1.5.0
RUN apt-get update && apt-get install -y --no-install-recommends unzip golang-go && rm -rf /var/lib/apt/lists/* && \
    GOBIN=/usr/local/bin go install -ldflags "-X main.ReleaseVersion=${GIT_SIZER_VERSION}" github.com/github/git-sizer@v${GIT_SIZER_VERSION}

COPY src/tools/git-sizer/ /caldera/src/tools/git-sizer/
WORKDIR /caldera/src/tools/git-sizer

# Symlink so the Makefile's bin/git-sizer resolves
RUN mkdir -p bin && ln -sf /usr/local/bin/git-sizer bin/git-sizer

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
