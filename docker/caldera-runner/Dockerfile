FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl git gnupg && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

COPY scripts/docker_runner.py /caldera/scripts/docker_runner.py

WORKDIR /caldera

ENTRYPOINT ["python", "scripts/docker_runner.py"]
