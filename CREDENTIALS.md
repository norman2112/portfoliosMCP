# Finding Your Planview Portfolios API Credentials

This guide explains where to find the OAuth credentials needed to use the Planview Portfolios MCP server. The server is hosted on FastMCP Cloud at `https://portfolios-mcp.fastmcp.app/mcp`, so you only need to configure your credentials in your MCP client (e.g., Claude Desktop).

## Required Credentials

You need three values to authenticate with the Planview Portfolios API:

1. **Client ID** - Your OAuth application identifier
2. **Client Secret** - Your OAuth application secret (keep this secure!)
3. **Tenant ID** - Your organization's unique identifier in Planview

## Where to Find Them

### Option 1: Planview Admin Portal

If you have administrative access to Planview Portfolios:

1. **Log into Planview Portfolios** as an administrator
2. **Navigate to Administration**:
   - Look for "API Settings", "Integrations", or "Developer Settings"
   - May be under: Settings → Integrations → API Credentials
3. **Create or View OAuth Client**:
   - If no OAuth client exists, create a new one
   - Note the **Client ID** and **Client Secret** (you may only see the secret once!)
   - The **Tenant ID** is usually displayed in the admin area or in your account settings

### Option 2: Contact Your Planview Administrator

If you don't have admin access:

1. **Contact your organization's Planview administrator**
2. **Request the following**:
   - OAuth Client ID and Client Secret (or ask them to create an OAuth application for you)
   - Your organization's Tenant ID
3. **Specify the use case**: Let them know you're building an MCP server integration

### Option 3: Planview Developer Portal

1. **Visit the Planview Developer Portal**: https://developer.planview.com
2. **Register for API access** (if required)
3. **Follow the registration process** to obtain credentials
4. **Check documentation** for your specific Planview instance type

## Common Locations in Planview UI

The exact location varies by Planview version and configuration, but typically look for:

- **Settings** → **Integrations** → **API Applications**
- **Administration** → **Security** → **OAuth Clients**
- **Developer Tools** → **API Credentials**
- **System Settings** → **API Configuration**

## Tenant ID Location

The Tenant ID is often found in:

- Your Planview URL (e.g., `https://yourcompany.planview.com` - the subdomain may indicate it)
- Account settings or profile page
- Organization information in admin panel
- Provided by your Planview administrator

## Security Best Practices

⚠️ **Important Security Notes**:

- **Never commit credentials to version control** - use `.env` file (which should be in `.gitignore`)
- **Client Secret is sensitive** - treat it like a password
- **Rotate credentials** if they're ever exposed
- **Use environment variables** or secure credential management tools
- **Limit API access** to only what's needed

## Testing Your Credentials

Once you have your credentials, you can test them in two ways:

1. **Via the MCP Server**: Configure your credentials in Claude Desktop (or your MCP client) and try using one of the available tools. If authentication fails, you'll see an error message.

2. **Local Testing Script** (if running locally for development):
   ```bash
   # Set your credentials in .env file first
   python get_token.py
   ```
   
   If the script succeeds, your credentials are correct and ready to use!

## Troubleshooting

**"Invalid OAuth credentials" error:**
- Double-check Client ID and Client Secret for typos
- Ensure there are no extra spaces when copying
- Verify the credentials haven't expired or been rotated

**"OAuth credentials not configured" error:**
- Make sure your `.env` file has `PLANVIEW_CLIENT_ID` and `PLANVIEW_CLIENT_SECRET` set
- Check that `USE_OAUTH=true` is set (or remove it, as `true` is the default)

**"Tenant ID not found" error:**
- Verify `PLANVIEW_TENANT_ID` is set in your `.env` file
- Contact your administrator if you're unsure of your Tenant ID

## Still Need Help?

- **Planview Support**: Contact Planview support for API access questions
- **Planview Developer Portal**: https://developer.planview.com
- **Your Organization's IT/Admin Team**: They may have documentation specific to your Planview setup

