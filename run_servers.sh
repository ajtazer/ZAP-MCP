#!/bin/bash

# Exit on error
set -e

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if mcp-server is installed
if ! command -v mcp-server &> /dev/null; then
    echo "Error: mcp-server is not installed. Please run setup_mcp.sh first."
    exit 1
fi

# Start MCP server in the background
echo "Starting MCP server..."
mcp-server --config claude_desktop_config.json --model-dir ./models &
MCP_PID=$!

# Wait for MCP server to start
echo "Waiting for MCP server to start..."
sleep 2

# Check if MCP server is still running
if ! kill -0 $MCP_PID 2>/dev/null; then
    echo "Error: MCP server failed to start"
    exit 1
fi

# Start ZAP-MCP server
echo "Starting ZAP-MCP server..."
python3 run.py

# Cleanup on exit
trap "kill $MCP_PID 2>/dev/null || true" EXIT 