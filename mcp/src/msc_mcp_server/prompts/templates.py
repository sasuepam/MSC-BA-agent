"""MCP Prompt Templates — reusable prompt patterns for Codemie agents."""

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register prompt templates on the MCP server."""

    @mcp.prompt()
    def mulesoft_api_review(api_spec: str) -> str:
        """Review a MuleSoft API specification (RAML/OAS) for best practices."""
        return (
            "You are a senior MuleSoft API designer at MSC Cruises. "
            "Review the following API specification for:\n"
            "- Naming conventions (kebab-case resources, camelCase fields)\n"
            "- REST best practices (proper HTTP methods, status codes)\n"
            "- Pagination, error handling, versioning\n"
            "- Security (OAuth2, client credentials)\n"
            "- MuleSoft Anypoint Exchange publishability\n\n"
            f"API Specification:\n```\n{api_spec}\n```"
        )

    @mcp.prompt()
    def jira_story_from_requirements(requirements: str) -> str:
        """Generate Jira user stories from business requirements."""
        return (
            "You are a Business Analyst at MSC Cruises IT. "
            "Convert the following business requirements into well-structured Jira user stories. "
            "Each story should include:\n"
            "- Title (concise)\n"
            "- User story format: As a [role], I want [feature], so that [benefit]\n"
            "- Acceptance criteria (Given/When/Then)\n"
            "- Story points estimate (1/2/3/5/8/13)\n\n"
            f"Requirements:\n{requirements}"
        )

    @mcp.prompt()
    def sprint_report(sprint_data: str) -> str:
        """Generate a sprint report summary for management."""
        return (
            "You are a project manager at MSC Cruises IT. "
            "Create a concise sprint report for stakeholders based on the following data. "
            "Include: sprint goal status, completed stories, carry-overs, blockers, "
            "velocity trend, and recommendations.\n\n"
            f"Sprint Data:\n{sprint_data}"
        )
