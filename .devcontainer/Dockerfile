FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.7.1

WORKDIR /workspace
CMD ["bash"]
