# ZAP-MCP: Model Context Protocol for OWASP ZAP

A FastAPI-based server that provides a Model Context Protocol (MCP) interface for OWASP ZAP, enabling AI-driven security testing and analysis.

## Project Structure

```
ZAP-MCP/
├── zap_mcp/                    # Main package directory
│   ├── api/                    # API routes and endpoints
│   │   └── routes.py          # API route definitions and handlers
│   ├── core/                   # Core functionality
│   │   ├── auth.py            # Authentication and authorization
│   │   ├── config.py          # Configuration management
│   │   └── mcp.py             # MCP protocol implementation
│   ├── models/                 # Data models
│   │   └── mcp.py             # Pydantic models for MCP messages
│   ├── services/              # External service integrations
│   │   └── zap_service.py     # OWASP ZAP service integration
│   ├── templates/             # HTML templates
│   │   └── index.html         # Main dashboard template
│   └── utils/                 # Utility functions
├── claude_integration.py      # Claude AI integration script
├── run.py                     # Application entry point
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── .env.example              # Example environment variables
└── zap_root_ca.cer           # ZAP root certificate
```

## Features

- FastAPI-based REST API
- OAuth2 authentication
- Real-time scan status updates via SSE
- HTML dashboard
- Claude AI integration for scan analysis
- Support for multiple scan types (active, passive, AJAX)
- Configurable scan parameters
- Multiple report formats (HTML, JSON, XML, Markdown)

## Prerequisites

- Python 3.8+
- OWASP ZAP installed and running
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/zap-mcp.git
cd zap-mcp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and configure it:
```bash
cp .env.example .env
```

5. Edit `.env` with your configuration:
```env
# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=false

# ZAP settings
ZAP_API_URL=http://127.0.0.1:8080
ZAP_API_KEY=your_zap_api_key

# Security settings
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MCP settings
MCP_VERSION=1.0
MAX_CONCURRENT_SCANS=5
SCAN_TIMEOUT=3600

# Report settings
REPORT_DIR=reports
DEFAULT_REPORT_FORMAT=html

# Logging settings
LOG_LEVEL=INFO
LOG_FILE=zap_mcp.log
```

## Running the Server

1. Start OWASP ZAP:
```bash
# Start ZAP in daemon mode
zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true
```

2. Start the MCP server:
```bash
python run.py
```

3. Access the dashboard:
- Open http://localhost:8000 in your browser
- Use the default credentials (test/test) to log in

## Using the Claude Integration

1. Make sure both ZAP and the MCP server are running

2. Run the Claude integration script:
```bash
python claude_integration.py
```

3. Enter the target URL when prompted

4. The script will:
   - Start a security scan
   - Monitor scan progress
   - Generate results and report
   - Create a prompt for Claude analysis

5. Copy the generated prompt and paste it into Claude Desktop

## API Endpoints

- `GET /`: HTML dashboard
- `GET /health`: Health check endpoint
- `GET /events`: SSE endpoint for real-time updates
- `POST /api/v1/token`: Get authentication token
- `POST /api/v1/scan/start`: Start a new scan
- `GET /api/v1/scan/{scan_id}/status`: Get scan status
- `GET /api/v1/scan/{scan_id}/results`: Get scan results
- `POST /api/v1/reports/generate`: Generate a report

## Security Considerations

- Always use HTTPS in production
- Keep your ZAP API key secure
- Use strong passwords and tokens
- Regularly update dependencies
- Monitor server logs for suspicious activity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 