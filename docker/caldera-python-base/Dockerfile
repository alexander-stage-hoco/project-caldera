FROM python:3.12-slim
WORKDIR /caldera

RUN apt-get update && \
    apt-get install -y --no-install-recommends git make curl && \
    rm -rf /var/lib/apt/lists/*

COPY src/common/ /caldera/src/common/
COPY src/shared/ /caldera/src/shared/
COPY src/tools/Makefile.common /caldera/src/tools/Makefile.common

RUN pip install --no-cache-dir jsonschema

ENV PYTHONPATH=/caldera/src
