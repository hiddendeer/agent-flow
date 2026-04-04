# Frontend Dockerfile - 优化版
# 支持国内网络环境，增加超时和重试配置

ARG PNPM_STORE_PATH=/root/.local/share/pnpm/store
ARG NPM_REGISTRY

# ── Base: shared setup ────────────────────────────────────────────────────────
FROM node:22-alpine AS base
ARG PNPM_STORE_PATH
ARG NPM_REGISTRY

# 安装ca证书以支持HTTPS
RUN apk add --no-cache ca-certificates wget

# Configure corepack registry before installing pnpm
RUN if [ -n "${NPM_REGISTRY}" ]; then \
      export COREPACK_NPM_REGISTRY="${NPM_REGISTRY}"; \
    fi && \
    corepack enable && corepack install -g pnpm@10.26.2

RUN pnpm config set store-dir ${PNPM_STORE_PATH}

# 使用国内镜像源（如果未指定）
RUN if [ -n "${NPM_REGISTRY}" ]; then \
      pnpm config set registry "${NPM_REGISTRY}"; \
    else \
      pnpm config set registry "https://registry.npmmirror.com"; \
    fi

# 配置网络超时和重试
RUN pnpm config set fetch-timeout 600000 && \
    pnpm config set fetch-retries 5 && \
    pnpm config set fetch-retry-mintimeout 10000 && \
    pnpm config set fetch-retry-maxtimeout 60000

WORKDIR /app
COPY frontend ./frontend

# ── Dev: install only, CMD is overridden by docker-compose ───────────────────
FROM base AS dev
# 使用--no-frozen-lockfile避免lockfile问题，增加网络容错性
RUN cd /app/frontend && pnpm install --no-frozen-lockfile --no-strict-peer-dependencies
EXPOSE 3000

# ── Builder: install + compile Next.js ───────────────────────────────────────
FROM base AS builder
RUN cd /app/frontend && pnpm install --no-frozen-lockfile --no-strict-peer-dependencies
# Skip env validation — runtime vars are injected by nginx/container
RUN cd /app/frontend && SKIP_ENV_VALIDATION=1 pnpm build

# ── Prod: minimal runtime with pre-built output ───────────────────────────────
FROM node:22-alpine AS prod
ARG PNPM_STORE_PATH
ARG NPM_REGISTRY
RUN if [ -n "${NPM_REGISTRY}" ]; then \
      export COREPACK_NPM_REGISTRY="${NPM_REGISTRY}"; \
    fi && \
    corepack enable && corepack install -g pnpm@10.26.2
RUN pnpm config set store-dir ${PNPM_STORE_PATH}
RUN if [ -n "${NPM_REGISTRY}" ]; then pnpm config set registry "${NPM_REGISTRY}"; fi
WORKDIR /app
COPY --from=builder /app/frontend ./frontend
EXPOSE 3000
CMD ["sh", "-c", "cd /app/frontend && pnpm start"]
