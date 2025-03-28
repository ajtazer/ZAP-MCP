#!/bin/bash

# Exit on error
set -e

echo "Setting up MCP server..."

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create models directory if it doesn't exist
mkdir -p models

# Install MCP server dependencies
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

# Install MCP server in development mode
echo "Installing MCP server..."
python3 -m pip install -e mcp

# Find the MCP server executable
echo "Locating MCP server executable..."
PYTHON_PATH=$(which python3)
PYTHON_DIR=$(dirname "$PYTHON_PATH")
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
MCP_SERVER_EXEC="$SITE_PACKAGES/mcp/mcp_server.py"

# Verify the executable exists
if [ ! -f "$MCP_SERVER_EXEC" ]; then
    echo "Error: Could not find MCP server executable at $MCP_SERVER_EXEC"
    echo "Checking alternative locations..."
    
    # Try to find the executable in the Python environment
    MCP_SERVER_EXEC=$(find "$SITE_PACKAGES" -name "mcp_server.py" 2>/dev/null | head -n 1)
    
    if [ -z "$MCP_SERVER_EXEC" ] || [ ! -f "$MCP_SERVER_EXEC" ]; then
        echo "Error: Could not find MCP server executable. Please check the installation."
        echo "Checking package contents..."
        python3 -c "import mcp; print('MCP package location:', mcp.__file__)"
        python3 -c "import mcp; print('MCP package contents:', mcp.__path__)"
        exit 1
    fi
fi

echo "Found MCP server executable at: $MCP_SERVER_EXEC"

# Create a local bin directory if it doesn't exist
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

# Create a wrapper script in the local bin directory
echo "Creating wrapper script..."
cat > "$LOCAL_BIN/mcp-server" << EOF
#!/bin/bash
"$PYTHON_PATH" "$MCP_SERVER_EXEC" "\$@"
EOF

# Make the wrapper script executable
chmod +x "$LOCAL_BIN/mcp-server"

# Add local bin to PATH if not already present
if ! grep -q "export PATH=\$HOME/.local/bin:\$PATH" "$HOME/.zshrc" 2>/dev/null; then
    echo "Adding ~/.local/bin to PATH..."
    echo 'export PATH=$HOME/.local/bin:$PATH' >> "$HOME/.zshrc"
    echo "Please run 'source ~/.zshrc' to update your PATH"
fi

echo "MCP server setup complete!"
echo "You can now run: mcp-server --config claude_desktop_config.json --model-dir ./models"
echo "Note: You may need to run 'source ~/.zshrc' to update your PATH"

# Verify the installation
if command -v mcp-server &> /dev/null; then
    echo "Installation verified successfully!"
else
    echo "Warning: Installation may not have completed successfully. Please check the errors above."
    echo "Try running 'source ~/.zshrc' to update your PATH"
    exit 1
fi 