FROM python:3.12-slim

# Install pnpm
RUN apt-get update && apt-get install -y curl git \
    && curl -fsSL https://get.pnpm.io/install.sh | bash - \
    && ln -s /root/.local/share/pnpm/pnpm /usr/local/bin/pnpm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.7.1

WORKDIR /workspace
CMD ["bash"]
