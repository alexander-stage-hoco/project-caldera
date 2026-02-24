FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends docker.io git && \
    rm -rf /var/lib/apt/lists/*

COPY scripts/docker_runner.py /caldera/scripts/docker_runner.py

WORKDIR /caldera

ENTRYPOINT ["python", "scripts/docker_runner.py"]
