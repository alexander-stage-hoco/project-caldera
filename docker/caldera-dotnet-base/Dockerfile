FROM mcr.microsoft.com/dotnet/sdk:8.0

WORKDIR /caldera

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-venv python3-pip git make curl && \
    rm -rf /var/lib/apt/lists/*

COPY src/common/ /caldera/src/common/
COPY src/shared/ /caldera/src/shared/
COPY src/tools/Makefile.common /caldera/src/tools/Makefile.common

RUN python3 -m pip install --no-cache-dir --break-system-packages jsonschema

ENV PYTHONPATH=/caldera/src
