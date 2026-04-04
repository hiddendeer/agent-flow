#!/usr/bin/env bash
#
# deploy-backend-only.sh - Deploy DeerFlow backend services only (no frontend, no sandbox)
# 用法: ./scripts/deploy-backend-only.sh [up|down|logs]

set -e

CMD="${1:-up}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DOCKER_DIR="$REPO_ROOT/docker"
COMPOSE_CMD="docker compose -p deer-flow -f $DOCKER_DIR/docker-compose-backend-only.yaml"

# ── Colors ────────────────────────────────────────────────────────────────────

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── Environment Variables ─────────────────────────────────────────────────────

if [ -z "$DEER_FLOW_HOME" ]; then
    export DEER_FLOW_HOME="$REPO_ROOT/backend/.deer-flow"
fi
echo -e "${BLUE}DEER_FLOW_HOME=$DEER_FLOW_HOME${NC}"
mkdir -p "$DEER_FLOW_HOME"

if [ -z "$DEER_FLOW_REPO_ROOT" ]; then
    export DEER_FLOW_REPO_ROOT="$REPO_ROOT"
fi

if [ -z "$DEER_FLOW_CONFIG_PATH" ]; then
    export DEER_FLOW_CONFIG_PATH="$REPO_ROOT/config.yaml"
fi

if [ ! -f "$DEER_FLOW_CONFIG_PATH" ]; then
    echo -e "${RED}✗ config.yaml not found at $DEER_FLOW_CONFIG_PATH${NC}"
    echo "Please run 'make config' first"
    exit 1
fi
echo -e "${GREEN}✓ config.yaml: $DEER_FLOW_CONFIG_PATH${NC}"

if [ -z "$DEER_FLOW_EXTENSIONS_CONFIG_PATH" ]; then
    export DEER_FLOW_EXTENSIONS_CONFIG_PATH="$REPO_ROOT/extensions_config.json"
fi

if [ ! -f "$DEER_FLOW_EXTENSIONS_CONFIG_PATH" ]; then
    if [ -f "$REPO_ROOT/extensions_config.json" ]; then
        cp "$REPO_ROOT/extensions_config.json" "$DEER_FLOW_EXTENSIONS_CONFIG_PATH"
    else
        echo '{"mcpServers":{},"skills":{}}' > "$DEER_FLOW_EXTENSIONS_CONFIG_PATH"
    fi
fi
echo -e "${GREEN}✓ extensions_config.json: $DEER_FLOW_EXTENSIONS_CONFIG_PATH${NC}"

# ── Commands ─────────────────────────────────────────────────────────────────

case "$CMD" in
    up)
        echo "=========================================="
        echo "  DeerFlow Backend Deployment"
        echo "=========================================="
        echo ""
        echo -e "${BLUE}Services: gateway, langgraph${NC}"
        echo ""
        echo "Building and starting containers..."
        echo ""

        $COMPOSE_CMD up --build -d --remove-orphans

        echo ""
        echo "=========================================="
        echo "  DeerFlow Backend is running!"
        echo "=========================================="
        echo ""
        echo "  📡 Gateway API: http://localhost:8001"
        echo "  🤖 LangGraph:   http://localhost:2024"
        echo "  📚 API Docs:    http://localhost:8001/docs"
        echo ""
        echo "  Manage:"
        echo "    ./scripts/deploy-backend-only.sh logs  - View logs"
        echo "    ./scripts/deploy-backend-only.sh down  - Stop services"
        echo ""
        ;;

    down)
        echo "Stopping DeerFlow backend services..."
        $COMPOSE_CMD down
        echo -e "${GREEN}✓ Services stopped${NC}"
        ;;

    logs)
        echo -e "${BLUE}Showing logs (Ctrl+C to exit)${NC}"
        $COMPOSE_CMD logs -f
        ;;

    *)
        echo "Usage: $0 [up|down|logs]"
        echo ""
        echo "Commands:"
        echo "  up    - Build and start backend services"
        echo "  down  - Stop and remove containers"
        echo "  logs  - View logs"
        exit 1
        ;;
esac
