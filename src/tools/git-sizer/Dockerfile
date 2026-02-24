FROM caldera-python-base:latest

RUN apt-get update && apt-get install -y --no-install-recommends unzip && rm -rf /var/lib/apt/lists/*

ARG GIT_SIZER_VERSION=1.5.0
RUN curl -sL "https://github.com/github/git-sizer/releases/download/v${GIT_SIZER_VERSION}/git-sizer-${GIT_SIZER_VERSION}-linux-amd64.zip" \
    -o /tmp/git-sizer.zip && unzip -o /tmp/git-sizer.zip -d /usr/local/bin && rm /tmp/git-sizer.zip

COPY src/tools/git-sizer/ /caldera/src/tools/git-sizer/
WORKDIR /caldera/src/tools/git-sizer

# Symlink so the Makefile's bin/git-sizer resolves
RUN mkdir -p bin && ln -s /usr/local/bin/git-sizer bin/git-sizer

RUN make setup

ENTRYPOINT ["make", "analyze", "SKIP_SETUP=1", \
    "REPO_PATH=/repo", "OUTPUT_DIR=/output"]
