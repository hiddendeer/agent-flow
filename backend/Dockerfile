# Backend Dockerfile — multi-stage build

# ── 全局变量定义 (必须在第一个 FROM 之前) ───────────────────────────────────
ARG UV_INSTALL_METHOD=image
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.7.20

# ── 基础 UV 定义 (用于海外服务器) ─────────────────────────────────────────────
FROM ${UV_IMAGE} AS uv-bin-image

# ── 腾讯云加速 UV 定义 (用于国内服务器) ────────────────────────────────────────
FROM python:3.12-slim-bookworm AS uv-bin-pip
ARG UV_INDEX_URL=https://pypi.org/simple
RUN pip install uv --index-url ${UV_INDEX_URL} && cp /usr/local/bin/uv /usr/local/bin/uvx /

# ── 最终 UV 提供者选择 ────────────────────────────────────────────────────────
FROM uv-bin-${UV_INSTALL_METHOD} AS uv-source

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

ARG NODE_MAJOR=22
ARG APT_MIRROR
ARG UV_INDEX_URL

# Optionally override apt mirror for restricted networks
RUN if [ -n "${APT_MIRROR}" ]; then \
      sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || true; \
      sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list 2>/dev/null || true; \
    fi

# Install build tools + Node.js
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    gnupg \
    ca-certificates \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 从选定的 uv-source 拷贝
COPY --from=uv-source /uv /uvx /usr/local/bin/

WORKDIR /app
COPY backend ./backend

RUN --mount=type=cache,target=/root/.cache/uv \
    sh -c "cd backend && UV_INDEX_URL=${UV_INDEX_URL:-https://pypi.org/simple} uv sync"

# ── Stage 2: Dev ──────────────────────────────────────────────────────────────
FROM builder AS dev
COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker
EXPOSE 8001 2024
CMD ["sh", "-c", "cd backend && PYTHONPATH=. uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001"]

# ── Stage 3: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm
COPY --from=builder /usr/bin/node /usr/bin/node
COPY --from=builder /usr/lib/node_modules /usr/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/bin/npx
COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker

COPY --from=uv-source /uv /uvx /usr/local/bin/

WORKDIR /app
COPY --from=builder /app/backend ./backend
EXPOSE 8001 2024
CMD ["sh", "-c", "cd backend && PYTHONPATH=. uv run --no-sync uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001"]
