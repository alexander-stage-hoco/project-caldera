FROM caldera-python-base:latest

RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-21-jre-headless unzip && \
    rm -rf /var/lib/apt/lists/* && \
    ln -s /usr/lib/jvm/java-21-openjdk-* /usr/lib/jvm/java-21-openjdk

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk
