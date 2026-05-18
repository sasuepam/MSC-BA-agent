"""Server configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """MCP server configuration. All values can be set via environment variables prefixed with MSC_."""

    model_config = SettingsConfigDict(
        env_prefix="MSC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    server_name: str = "msc-mcp-server"
    transport: str = "sse"  # "sse" or "stdio"
    debug: bool = False

    # Authentication token that Codemie must send to access this server
    api_token: str = ""

    # --- Downstream integration credentials (added as integrations are built) ---

    # Jira
    jira_url: str = ""
    jira_token: str = ""
    jira_email: str = ""

    # Confluence — Production (read-only recommended)
    confluence_url: str = ""
    confluence_email: str = ""
    confluence_token: str = ""

    # Confluence — Sandbox (for writing/testing)
    confluence_sandbox_url: str = ""
    confluence_sandbox_email: str = ""
    confluence_sandbox_token: str = ""

    # MuleSoft Anypoint
    anypoint_url: str = "https://anypoint.mulesoft.com"
    anypoint_client_id: str = ""
    anypoint_client_secret: str = ""

    # Git provider
    git_provider: str = ""  # "github", "gitlab", "bitbucket"
    git_token: str = ""
    git_base_url: str = ""

    # Microsoft Graph (O365)
    ms_tenant_id: str = ""
    ms_client_id: str = ""
    ms_client_secret: str = ""


settings = ServerSettings()
