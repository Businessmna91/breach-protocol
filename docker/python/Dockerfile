FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    findutils grep coreutils && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash agent && \
    pip install --no-cache-dir --upgrade pip
USER agent
ENV PATH="/home/agent/.local/bin:${PATH}"
WORKDIR /home/agent
