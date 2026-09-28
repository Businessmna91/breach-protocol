FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    findutils grep sed gawk coreutils procps less vim-tiny curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash agent
USER agent
WORKDIR /home/agent
