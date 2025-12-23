# Planview Portfolios MCP Server

A Model Context Protocol (MCP) server for integrating with Planview Portfolios, built with [FastMCP](https://github.com/jlowin/fastmcp). 

**🌐 FastMCP Cloud URL**: `https://portfolios-mcp.fastmcp.app/mcp`

This server is hosted on FastMCP Cloud, so no local installation is required. Simply configure your MCP client (e.g., Claude Desktop) to connect to the cloud instance with your Planview API credentials.

## Features

### Project & Portfolio Management
- **List Projects**: Query projects with filtering by portfolio, status, and more
- **Get Project**: Retrieve detailed information about a specific project
- **Create Project**: Create new projects with comprehensive configuration
- **Update Project**: Modify existing project details and settings

### Resource Management
- **List Resources**: Browse team members with filtering by department, role, and availability
- **Get Resource**: View detailed resource information including allocations and capacity
- **Allocate Resource**: Assign resources to projects with flexible allocation percentages

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10 or higher** (for local installation)
  - **macOS/Linux**: Usually pre-installed. Verify with `python3 --version` or install via Homebrew: `brew install python3`
  - **Windows**: Download from [python.org](https://www.python.org/downloads/) or use Microsoft Store. Ensure "Add Python to PATH" is checked during installation
- **Planview Portfolios API credentials** (OAuth client_id, client_secret, and tenant ID)
- **Claude Desktop** installed (for MCP client usage)
  - **macOS**: Download from [claude.ai](https://claude.ai/download)
  - **Windows**: Download from [claude.ai](https://claude.ai/download)

## OAuth Authentication & Token Generation

The Planview Portfolios MCP server uses OAuth 2.0 client credentials flow for secure API authentication. You need to generate OAuth2 credentials in Planview Admin before using the MCP tools.

### Generating OAuth2 Credentials

To generate OAuth2 credentials for Planview Portfolios API access:

1. **Log into Planview Portfolios** as an administrator
   - Navigate to your Planview instance (e.g., `https://yourcompany.pvcloud.com`)

2. **Access the Admin Portal**:
   - Click on your user profile/avatar (usually top-right)
   - Select **"Administration"** or **"Admin"** from the menu
   - Alternatively, navigate directly to: `https://your-instance.pvcloud.com/admin`

3. **Navigate to OAuth Settings**:
   - In the Administration screen, look for **"API Settings"**, **"Integrations"**, or **"Security"**
   - Click on **"OAuth Clients"** or **"API Applications"** tab
   - The exact path may vary by Planview version:
     - **Settings** → **Integrations** → **API Applications**
     - **Administration** → **Security** → **OAuth Clients**
     - **Developer Tools** → **API Credentials**
     - **System Settings** → **API Configuration**

4. **Create OAuth2 Credentials**:
   - Click **"Create OAuth2 credentials"** or **"New OAuth Client"** button
   - Enter a descriptive **Name** for the credential (e.g., "MCP Server Integration" or "Claude Desktop Integration")
   - Select the appropriate **Application** type (usually **"Portfolios Integration"** or **"API Application"**)
   - Configure any required scopes or permissions (if applicable)
   - Click **"Create OAuth2 credentials"** or **"Save"**

5. **Copy Your Credentials**:
   - After creation, you'll see:
     - **Client ID**: A unique identifier (usually a UUID or alphanumeric string)
     - **Client Secret**: A secret key (usually longer, alphanumeric string)
   - Click the copy icons (📋) next to each field to copy them to your clipboard
   - **⚠️ CRITICAL SECURITY WARNING**: The Client Secret is only displayed once. If you close the dialog without copying it, you cannot retrieve it later and will need to create new credentials.
   - Store these credentials securely (see [Security Best Practices](#security-best-practices) below)

6. **Find Your Tenant ID**:
   - The Tenant ID is your organization's unique identifier in Planview
   - Common locations:
     - Displayed in the OAuth credentials dialog or admin panel
     - Visible in your Planview URL (e.g., `https://yourcompany.pvcloud.com` - the subdomain may indicate it)
     - Found in Account Settings → Organization Information
     - Provided by your Planview administrator
   - Copy and store this value securely

7. **Click Close** to exit the credentials dialog

### How OAuth Token Management Works

Once you have your OAuth2 credentials configured:

1. **Automatic Token Exchange**: The MCP server automatically exchanges your Client ID and Client Secret for an access token using the `client_credentials` grant type
2. **Token Caching**: Access tokens are cached in memory and reused until expiration
3. **Automatic Refresh**: Tokens are valid for **60 minutes** and are automatically refreshed:
   - When they expire (proactive refresh before expiry)
   - On 401 Unauthorized errors (automatic retry with fresh token)
4. **Seamless Operation**: You don't need to manually manage tokens - the server handles everything automatically

### Security Best Practices

⚠️ **Important Security Notes**:

- **Never commit credentials to version control**
  - Use environment variables in your Claude Desktop config (not committed)
  - If using `.env` file for local development, ensure it's in `.gitignore`
- **Client Secret is highly sensitive** - treat it like a password
  - Don't share it via email, chat, or unsecured channels
  - Don't paste it into public forums or documentation
- **Rotate credentials immediately** if they're ever exposed or compromised
- **Use environment variables** or secure credential management tools
- **Limit API access** to only what's needed - configure minimal required scopes/permissions
- **Regular credential audits** - periodically review and rotate credentials

### Obtaining API Credentials (Alternative Methods)

If you don't have administrative access:

**Option 1: Contact Your Planview Administrator**
- Request OAuth Client ID and Client Secret (or ask them to create an OAuth application for you)
- Request your organization's Tenant ID
- Specify the use case: "MCP server integration for Claude Desktop"

**Option 2: Planview Developer Portal**
- Visit the [Planview Developer Portal](https://developer.planview.com)
- Register for API access (if required)
- Follow the registration process to obtain credentials
- Check documentation for your specific Planview instance type

**Option 3: Check Existing Credentials**
- If your organization already has OAuth credentials, ask your administrator to share:
  - Client ID
  - Client Secret (if still available)
  - Tenant ID

## Installation & Setup

This MCP server can be run in two ways:
- **FastMCP Cloud** (easiest - no local installation required)
- **Local Installation** (recommended for development or custom configurations)

Choose the option that best fits your needs. Both options require the same OAuth credentials.

### Quick Start Checklist

- [ ] Obtain OAuth credentials (Client ID, Client Secret, Tenant ID) - see [OAuth Authentication & Token Generation](#oauth-authentication--token-generation) above
- [ ] Install Claude Desktop (if not already installed)
- [ ] Locate your Claude Desktop configuration file
- [ ] Add MCP server configuration with your credentials
- [ ] Restart Claude Desktop
- [ ] Test the connection

### Step 1: Get Your Planview API Credentials

Before configuring the MCP server, ensure you have:

1. **Client ID** (`PLANVIEW_CLIENT_ID`) - from OAuth credentials creation
2. **Client Secret** (`PLANVIEW_CLIENT_SECRET`) - from OAuth credentials creation  
3. **Tenant ID** (`PLANVIEW_TENANT_ID`) - your organization identifier
4. **API URL** (`PLANVIEW_API_URL`) - your Planview instance URL with `/polaris` path

**Need detailed help?** See:
- [OAuth Authentication & Token Generation](#oauth-authentication--token-generation) for step-by-step credential generation
- [CREDENTIALS.md](CREDENTIALS.md) for additional credential finding tips

### Step 2: Locate Your Claude Desktop Configuration File

The configuration file location depends on your operating system:

**macOS:**
- **Path**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Quick access**: 
  - Open Finder
  - Press `Cmd + Shift + G` (Go to Folder)
  - Paste: `~/Library/Application Support/Claude`
  - Open `claude_desktop_config.json` in a text editor

**Windows:**
- **Path**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Full path example**: `C:\Users\<YourUsername>\AppData\Roaming\Claude\claude_desktop_config.json`
- **Quick access**:
  - Press `Win + R` to open Run dialog
  - Type: `%APPDATA%\Claude`
  - Press Enter
  - Open `claude_desktop_config.json` in Notepad or your preferred text editor

**Linux:**
- **Path**: `~/.config/Claude/claude_desktop_config.json`
- **Quick access**: Open terminal and run `nano ~/.config/Claude/claude_desktop_config.json`

**Note**: If the file doesn't exist, create it. If the directory doesn't exist, create it first, then create the file.

## Usage

### Step 3: Configure Claude Desktop

You can run the MCP server locally or use the FastMCP Cloud instance. Choose the option that works best for you.

#### Option 1: FastMCP Cloud (Easiest - Recommended for Most Users)

This option requires no local installation. The server runs in the cloud, and you only need to configure Claude Desktop.

**macOS Configuration:**

1. Open `~/Library/Application Support/Claude/claude_desktop_config.json` in a text editor
2. Add or update the configuration:

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "url": "https://portfolios-mcp.fastmcp.app/mcp",
      "env": {
        "PLANVIEW_API_URL": "https://your-instance.pvcloud.com/polaris",
        "PLANVIEW_CLIENT_ID": "your_client_id_here",
        "PLANVIEW_CLIENT_SECRET": "your_client_secret_here",
        "PLANVIEW_TENANT_ID": "your_tenant_id_here",
        "USE_OAUTH": "true"
      }
    }
  }
}
```

**Windows Configuration:**

1. Open `%APPDATA%\Claude\claude_desktop_config.json` in Notepad or your preferred editor
2. Add or update the configuration (same JSON as above)

**Important Configuration Notes:**
- Replace all placeholder values with your actual credentials:
  - `PLANVIEW_API_URL`: Your Planview instance API base URL **including `/polaris` path** (e.g., `https://scdemo504.pvcloud.com/polaris`)
    - ✅ Correct: `https://scdemo504.pvcloud.com/polaris`
    - ❌ Incorrect: `https://scdemo504.pvcloud.com` (missing `/polaris`)
    - ❌ Incorrect: `https://scdemo504.pvcloud.com/polaris/` (trailing slash)
  - `PLANVIEW_CLIENT_ID`: Your OAuth Client ID (from Planview Admin)
  - `PLANVIEW_CLIENT_SECRET`: Your OAuth Client Secret (from Planview Admin)
  - `PLANVIEW_TENANT_ID`: Your Tenant ID
- Ensure JSON syntax is valid (use a JSON validator if unsure)
- If you have other MCP servers configured, add this entry to the existing `mcpServers` object

**Example with Multiple MCP Servers:**

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "url": "https://portfolios-mcp.fastmcp.app/mcp",
      "env": {
        "PLANVIEW_API_URL": "https://scdemo504.pvcloud.com/polaris",
        "PLANVIEW_CLIENT_ID": "abc123-def456-ghi789",
        "PLANVIEW_CLIENT_SECRET": "secret123456789",
        "PLANVIEW_TENANT_ID": "tenant-12345",
        "USE_OAUTH": "true"
      }
    },
    "another-server": {
      "command": "node",
      "args": ["/path/to/server.js"]
    }
  }
}
```

#### Option 2: Local Installation (Recommended for Development)

This option runs the MCP server locally on your machine. Useful for development, debugging, or custom configurations.

**Prerequisites for Local Installation:**

- Python 3.10 or higher installed
- Package installed: `pip install -e .`
- (Optional but recommended) Virtual environment set up

**Step 1: Install the Package**

**macOS/Linux:**
```bash
# Navigate to project directory
cd /path/to/portfolios-mcp-financials

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install the package
pip install -e .
```

**Windows:**
```cmd
REM Navigate to project directory
cd C:\path\to\portfolios-mcp-financials

REM Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

REM Install the package
pip install -e .
```

**Step 2: Find Your Python Path**

**macOS/Linux:**
```bash
# If using system Python
which python3
# Output example: /usr/bin/python3

# If using virtual environment
which python
# Output example: /Users/yourname/portfolios-mcp-financials/venv/bin/python3
```

**Windows:**
```cmd
REM If using system Python
where python
REM Output example: C:\Python311\python.exe

REM If using virtual environment
where python
REM Output example: C:\path\to\portfolios-mcp-financials\venv\Scripts\python.exe
```

**Step 3: Configure Claude Desktop**

**macOS Configuration (with virtual environment):**

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "command": "/Users/yourname/portfolios-mcp-financials/venv/bin/python3",
      "args": [
        "-m",
        "planview_portfolios_mcp.server"
      ],
      "env": {
        "PLANVIEW_API_URL": "https://your-instance.pvcloud.com/polaris",
        "PLANVIEW_CLIENT_ID": "your_client_id_here",
        "PLANVIEW_CLIENT_SECRET": "your_client_secret_here",
        "PLANVIEW_TENANT_ID": "your_tenant_id_here",
        "USE_OAUTH": "true"
      }
    }
  }
}
```

**macOS Configuration (system Python):**

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "command": "python3",
      "args": [
        "-m",
        "planview_portfolios_mcp.server"
      ],
      "env": {
        "PLANVIEW_API_URL": "https://your-instance.pvcloud.com/polaris",
        "PLANVIEW_CLIENT_ID": "your_client_id_here",
        "PLANVIEW_CLIENT_SECRET": "your_client_secret_here",
        "PLANVIEW_TENANT_ID": "your_tenant_id_here",
        "USE_OAUTH": "true"
      }
    }
  }
}
```

**Windows Configuration (with virtual environment):**

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "command": "C:\\path\\to\\portfolios-mcp-financials\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "planview_portfolios_mcp.server"
      ],
      "env": {
        "PLANVIEW_API_URL": "https://your-instance.pvcloud.com/polaris",
        "PLANVIEW_CLIENT_ID": "your_client_id_here",
        "PLANVIEW_CLIENT_SECRET": "your_client_secret_here",
        "PLANVIEW_TENANT_ID": "your_tenant_id_here",
        "USE_OAUTH": "true"
      }
    }
  }
}
```

**Windows Configuration (system Python):**

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "command": "python",
      "args": [
        "-m",
        "planview_portfolios_mcp.server"
      ],
      "env": {
        "PLANVIEW_API_URL": "https://your-instance.pvcloud.com/polaris",
        "PLANVIEW_CLIENT_ID": "your_client_id_here",
        "PLANVIEW_CLIENT_SECRET": "your_client_secret_here",
        "PLANVIEW_TENANT_ID": "your_tenant_id_here",
        "USE_OAUTH": "true"
      }
    }
  }
}
```

**Important Notes for Local Installation:**
- Use the **full path** to Python if using a virtual environment
- On Windows, use double backslashes (`\\`) or forward slashes (`/`) in paths
- Ensure the package is installed: `pip install -e .`
- Test the server manually: `python -m planview_portfolios_mcp.server` (should start without errors)
- See `CLAUDE_DESKTOP_SETUP.md` for additional troubleshooting tips

### Step 4: Restart Claude Desktop

After saving your configuration:

1. **macOS**: Quit Claude Desktop completely (`Cmd + Q`) and reopen it
2. **Windows**: Close Claude Desktop completely and reopen it
3. **Verify**: Start a new conversation and check if Planview tools are available

**Note**: Configuration changes only take effect after a full restart of Claude Desktop.

### Step 5: Verify Your Setup

After restarting Claude Desktop, verify everything is working:

1. **Start a new conversation** in Claude Desktop
2. **Check for MCP tools**: The Planview tools should be available (you may see them in Claude's tool list)
3. **Test with a simple query**: Try asking Claude:
   - "List my Planview projects"
   - "What Planview tools are available?"
   - "Help me get started with Planview Portfolios"

If you encounter errors, see the [Troubleshooting](#troubleshooting) section below.

## Local Development (Optional)

If you want to run the server locally for development, testing, or custom configurations:

### Prerequisites

- Python 3.10 or higher
- Git (for cloning the repository)
- Virtual environment (recommended)

### Setup Steps

**macOS/Linux:**

```bash
# 1. Clone or navigate to the project directory
cd /path/to/portfolios-mcp-financials

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install the package in development mode
pip install -e .

# 6. Create .env file (if it doesn't exist)
cp .env.example .env  # If .env.example exists
# Or create .env manually

# 7. Edit .env and add your Planview API credentials
# Use your preferred text editor:
nano .env
# or
vim .env
# or
code .env  # If using VS Code
```

**Windows:**

```cmd
REM 1. Navigate to the project directory
cd C:\path\to\portfolios-mcp-financials

REM 2. Create a virtual environment
python -m venv venv

REM 3. Activate the virtual environment
venv\Scripts\activate

REM 4. Install dependencies
pip install -r requirements.txt

REM 5. Install the package in development mode
pip install -e .

REM 6. Create .env file (if it doesn't exist)
copy .env.example .env
REM Or create .env manually using Notepad

REM 7. Edit .env and add your Planview API credentials
notepad .env
```

### .env File Format

Create a `.env` file in the project root with your credentials:

```env
PLANVIEW_API_URL=https://your-instance.pvcloud.com/polaris
PLANVIEW_CLIENT_ID=your_client_id_here
PLANVIEW_CLIENT_SECRET=your_client_secret_here
PLANVIEW_TENANT_ID=your_tenant_id_here
USE_OAUTH=true
```

**Important**: Never commit the `.env` file to version control. It should be in `.gitignore`.

### Running the Server Locally

**macOS/Linux:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the server
python -m planview_portfolios_mcp.server
```

**Windows:**
```cmd
REM Make sure virtual environment is activated
venv\Scripts\activate

REM Run the server
python -m planview_portfolios_mcp.server
```

The server will start and wait for stdio input from Claude Desktop. You can test it by configuring Claude Desktop to use the local server (see [Option 2: Local Installation](#option-2-local-installation-recommended-for-development) above).

### Testing OAuth Token Retrieval

To verify your credentials work correctly:

**macOS/Linux:**
```bash
# Make sure virtual environment is activated and .env is configured
source venv/bin/activate
python get_token.py  # If this script exists
```

**Windows:**
```cmd
venv\Scripts\activate
python get_token.py  # If this script exists
```

If the script succeeds and returns a token, your credentials are correct!

## Available Tools

### Project Management Tools

#### `list_projects`
List projects with optional filtering.

**Parameters:**
- `portfolio_id` (optional): Filter by portfolio ID
- `status` (optional): Filter by status (e.g., 'active', 'completed', 'on-hold')
- `limit` (default: 50): Maximum number of results

#### `get_project`
Get detailed information about a specific project.

**Parameters:**
- `project_id` (required): The unique identifier of the project

#### `create_project`
Create a new project.

**Parameters:**
- `name` (required): Project name
- `description` (optional): Project description
- `portfolio_id` (optional): Associated portfolio ID
- `start_date` (optional): Start date (ISO format: YYYY-MM-DD)
- `end_date` (optional): End date (ISO format: YYYY-MM-DD)
- `budget` (optional): Project budget

#### `update_project`
Update an existing project.

**Parameters:**
- `project_id` (required): The project to update
- `name` (optional): New project name
- `description` (optional): New description
- `status` (optional): New status
- `start_date` (optional): New start date
- `end_date` (optional): New end date
- `budget` (optional): New budget

### Resource Management Tools

#### `list_resources`
List available resources (team members).

**Parameters:**
- `department` (optional): Filter by department
- `role` (optional): Filter by role
- `available` (optional): Filter by availability (true/false)
- `limit` (default: 50): Maximum number of results

#### `get_resource`
Get detailed information about a specific resource.

**Parameters:**
- `resource_id` (required): The unique identifier of the resource

#### `allocate_resource`
Allocate a resource to a project.

**Parameters:**
- `resource_id` (required): The resource to allocate
- `project_id` (required): The target project
- `allocation_percentage` (required): Allocation percentage (0-100)
- `start_date` (required): Allocation start date (ISO format: YYYY-MM-DD)
- `end_date` (required): Allocation end date (ISO format: YYYY-MM-DD)
- `role` (optional): Role for this allocation

## Development

This section is for developers who want to contribute to or modify the server code.

### Running Tests

```bash
pytest
```

### Code Quality

Format code with Black:
```bash
black src/
```

Lint with Ruff:
```bash
ruff check src/
```

Type check with mypy:
```bash
mypy src/
```

### Project Structure

```
planview-portfolios-mcp/
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── src/
│   └── planview_portfolios_mcp/
│       ├── __init__.py
│       ├── server.py          # Main FastMCP server
│       ├── config.py           # Configuration management
│       ├── client.py           # Shared HTTP client with retry logic
│       ├── exceptions.py       # Custom exception types
│       ├── models.py           # Pydantic validation models
│       ├── logging_config.py   # Logging configuration
│       └── tools/
│           ├── __init__.py
│           ├── projects.py     # Project management tools
│           └── resources.py    # Resource management tools
└── tests/
    └── __init__.py
```

## Troubleshooting

### Common Issues and Solutions

#### Server Not Starting

**Symptoms**: Claude Desktop shows errors about the MCP server not starting, or tools don't appear.

**Solutions**:

**For Local Installation:**
- **Check Python path**: Verify the path in `claude_desktop_config.json` is correct
  - **macOS/Linux**: Run `which python3` to find the correct path
  - **Windows**: Run `where python` to find the correct path
- **Verify package installation**: Run `pip show planview-portfolios-mcp` or `pip list | grep planview`
- **Test server manually**: Run `python -m planview_portfolios_mcp.server` in terminal
  - Should start without errors (will wait for stdio input)
  - If errors occur, check the error message
- **Check virtual environment**: If using venv, ensure you're using the venv's Python path
- **Check Claude Desktop logs**: Look for error messages in Claude Desktop's console/debug output

**For FastMCP Cloud:**
- **Check internet connection**: Ensure you can reach `https://portfolios-mcp.fastmcp.app`
- **Verify JSON syntax**: Use a JSON validator to check your config file
- **Check Claude Desktop logs**: Look for connection errors

#### Authentication Errors

**Symptoms**: "Invalid OAuth credentials", "401 Unauthorized", or "OAuth credentials not configured" errors.

**Solutions**:
- **Double-check credentials**: Verify Client ID, Client Secret, and Tenant ID are correct
  - Check for typos or extra spaces when copying
  - Ensure credentials haven't expired or been rotated
- **Verify API URL format**: 
  - ✅ Correct: `https://scdemo504.pvcloud.com/polaris`
  - ❌ Wrong: `https://scdemo504.pvcloud.com` (missing `/polaris`)
  - ❌ Wrong: `https://scdemo504.pvcloud.com/polaris/` (trailing slash)
- **Check environment variables**: Ensure all required variables are set in your config:
  - `PLANVIEW_CLIENT_ID`
  - `PLANVIEW_CLIENT_SECRET`
  - `PLANVIEW_TENANT_ID`
  - `PLANVIEW_API_URL`
  - `USE_OAUTH` (should be `"true"` or can be omitted as it defaults to true)
- **Test credentials**: If running locally, test with `python get_token.py` (if available)
- **Regenerate credentials**: If credentials were exposed or compromised, create new ones in Planview Admin

#### Module Not Found Errors

**Symptoms**: "ModuleNotFoundError" or "No module named 'planview_portfolios_mcp'" errors.

**Solutions**:
- **Install the package**: Run `pip install -e .` from the project directory
- **Check Python path**: Ensure Claude Desktop is using the Python where the package is installed
- **Verify virtual environment**: If using venv, ensure Claude Desktop config points to venv's Python
- **Check installation location**: Run `pip show planview-portfolios-mcp` to see where it's installed

#### Tools Not Appearing in Claude Desktop

**Symptoms**: Configuration looks correct, but Planview tools don't appear in Claude.

**Solutions**:
- **Restart Claude Desktop**: Configuration changes only take effect after a full restart
  - **macOS**: Quit completely (`Cmd + Q`) and reopen
  - **Windows**: Close completely and reopen
- **Check server status**: Verify the MCP server is starting without errors (check logs)
- **Verify configuration syntax**: Ensure JSON is valid (use a JSON validator)
- **Check for conflicting configs**: Ensure there are no duplicate server entries
- **Start new conversation**: MCP tools may only appear in new conversations after restart

#### JSON Configuration Errors

**Symptoms**: Claude Desktop fails to load configuration, or JSON parsing errors.

**Solutions**:
- **Validate JSON syntax**: Use an online JSON validator or your editor's JSON validator
- **Check for trailing commas**: JSON doesn't allow trailing commas in objects/arrays
- **Verify quotes**: Ensure all strings are in double quotes (`"`), not single quotes (`'`)
- **Check file encoding**: Ensure the file is saved as UTF-8
- **Backup and recreate**: If corrupted, backup your config and recreate it

#### Windows-Specific Issues

**Symptoms**: Path-related errors, Python not found, or permission errors on Windows.

**Solutions**:
- **Use forward slashes or double backslashes**: 
  - ✅ `C:/path/to/python.exe` or `C:\\path\\to\\python.exe`
  - ❌ `C:\path\to\python.exe` (single backslashes may cause issues)
- **Check Python PATH**: Ensure Python is in your system PATH, or use full path in config
- **Run as administrator**: If permission errors occur, try running Claude Desktop as administrator
- **Check file permissions**: Ensure you have write access to the config file location

#### macOS-Specific Issues

**Symptoms**: Permission errors, Python path issues, or file access problems.

**Solutions**:
- **Check Python installation**: Verify with `python3 --version`
- **Use full paths**: If using Homebrew Python, use full path like `/opt/homebrew/bin/python3` (Apple Silicon) or `/usr/local/bin/python3` (Intel)
- **Check file permissions**: Ensure you have read/write access to `~/Library/Application Support/Claude/`
- **Check Gatekeeper**: If Python was downloaded, you may need to allow it in System Preferences → Security & Privacy

### Getting Help

If you've tried the troubleshooting steps above and still have issues:

1. **Check the logs**: Claude Desktop may have error logs that provide more details
2. **Verify your setup**: Go through the [Quick Start Checklist](#quick-start-checklist) again
3. **Review documentation**: 
   - See [CREDENTIALS.md](CREDENTIALS.md) for credential-related issues
   - See [CLAUDE_DESKTOP_SETUP.md](CLAUDE_DESKTOP_SETUP.md) for detailed setup instructions
4. **Check Planview API status**: Ensure your Planview instance is accessible and API is enabled
5. **Contact support**: 
   - Open an issue on the repository
   - Contact Planview support for API access questions
   - Check the [Planview Developer Portal](https://developer.planview.com)

## Configuration Reference

### Environment Variables

When configuring the MCP server (either FastMCP Cloud or local), you can set these environment variables:

#### Required for OAuth Authentication

- **`PLANVIEW_CLIENT_ID`** (required): Your OAuth Client ID from Planview Admin
- **`PLANVIEW_CLIENT_SECRET`** (required): Your OAuth Client Secret from Planview Admin
- **`PLANVIEW_TENANT_ID`** (required): Your organization's Tenant ID

#### Optional Configuration

- **`PLANVIEW_API_URL`** (optional): Base URL for Planview API including `/polaris` path
  - Example: `https://scdemo504.pvcloud.com/polaris`
  - Default: `https://api.planview.com` (if not specified)
  - **Important**: Must include `/polaris` path, no trailing slash
- **`USE_OAUTH`** (optional): Enable OAuth authentication
  - Default: `true`
  - Set to `"true"` explicitly or omit (both work)
- **`PLANVIEW_API_KEY`** (deprecated): Legacy API key authentication
  - **Not recommended**: Use OAuth instead
  - Only use if OAuth is not available for your instance

#### Local Development Only

These options are only available when running the server locally:

- **`API_TIMEOUT`** (optional): HTTP request timeout in seconds
  - Default: `30`
- **`MAX_RETRIES`** (optional): Maximum number of retry attempts for failed requests
  - Default: `3`

### OAuth Token Management

The MCP server automatically handles OAuth token lifecycle:

- **Token Exchange**: Automatically exchanges Client ID and Secret for access token using `client_credentials` grant type
- **Token Caching**: Tokens are cached in memory and reused until expiration
- **Token Lifetime**: Access tokens are valid for **60 minutes**
- **Automatic Refresh**: Tokens are automatically refreshed:
  - Proactively before expiration
  - On 401 Unauthorized errors (with automatic retry)
- **Seamless Operation**: No manual token management required

### Configuration Examples

See the [Configuring Claude Desktop](#step-3-configure-claude-desktop) section above for complete configuration examples for both macOS and Windows.

## License

MIT

## Contributing

Contributions are welcome! Please ensure all tests pass and code is formatted with Black before submitting.

## Support

For issues or questions about this MCP server, please open an issue on the repository.

For Planview Portfolios API documentation, visit the official Planview developer portal.
