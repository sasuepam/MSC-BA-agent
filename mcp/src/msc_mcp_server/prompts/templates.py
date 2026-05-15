"""MCP Prompt Templates — reusable prompt patterns for the BA agent."""

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register prompt templates on the MCP server."""

    @mcp.prompt()
    def functional_spec_from_ia(ia_content: str) -> str:
        """Generate a functional specification from an Interface Agreement document."""
        return (
            "You are a senior Business Analyst at MSC Cruises working on the DTTP MuleSoft integration program. "
            "Generate a structured functional specification from the following Interface Agreement content. "
            "The spec must include:\n"
            "- Feature Summary and business context\n"
            "- Solution Scope (in-scope, out-of-scope, assumptions, constraints)\n"
            "- Functional Requirements as use cases (actor, trigger, flow, alt flows, errors)\n"
            "- High-Level Impacts on upstream/downstream systems\n"
            "- Test Scenarios (happy path + edge cases)\n"
            "- Non-Functional Requirements (performance, security, availability)\n"
            "- Open Gaps\n\n"
            f"Interface Agreement Content:\n{ia_content}"
        )

    @mcp.prompt()
    def jira_story_from_requirements(requirements: str) -> str:
        """Generate Jira user stories from business requirements."""
        return (
            "You are a Business Analyst at MSC Cruises IT working on the DTTP MuleSoft program. "
            "Convert the following business requirements into well-structured Jira user stories. "
            "Each story should include:\n"
            "- Title (concise)\n"
            "- User story format: As a [role], I want [feature], so that [benefit]\n"
            "- Acceptance criteria (Given/When/Then)\n"
            "- Story points estimate (1/2/3/5/8/13)\n"
            "- Labels: identify if it is a new feature or change request\n\n"
            f"Requirements:\n{requirements}"
        )

    @mcp.prompt()
    def change_request_from_spec(change_description: str) -> str:
        """Generate a Change Request document from a change description."""
        return (
            "You are a Business Analyst at MSC Cruises IT. "
            "Create a structured Change Request document from the following change description. "
            "Include: Change Scope (what/current state/desired state/interfaces impacted), "
            "Rationale, Impact Assessment (business/technical/risk), "
            "Resources required, Acceptance Criteria (BDD format), "
            "and Open Questions.\n\n"
            f"Change Description:\n{change_description}"
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
