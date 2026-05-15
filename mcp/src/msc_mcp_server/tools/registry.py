"""Tool registry — auto-discovers and registers all tool modules.

To add a new tool module:
1. Create a new file in src/msc_mcp_server/tools/ (e.g., jira.py)
2. Define a `register(mcp: FastMCP) -> None` function in it
3. Add the module name to TOOL_MODULES below
"""

import importlib
import logging

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

TOOL_MODULES: list[str] = [
    "demo",
    "confluence",    # read + write
    "jira",          # read + write
    "ia_extractor",  # deterministic IA/PAPI page parser
    "confluence_md", # Confluence HTML → clean Markdown converter
    # "anypoint",      # Phase 3
    # "office365",     # Phase 4
    # "git_tools",     # Phase 5
]


def register_all_tools(mcp: FastMCP) -> None:
    """Import each tool module and call its register() function."""
    for module_name in TOOL_MODULES:
        fqn = f"msc_mcp_server.tools.{module_name}"
        try:
            mod = importlib.import_module(fqn)
            mod.register(mcp)
            logger.info("Registered tool module: %s", module_name)
        except Exception:
            logger.exception("Failed to register tool module: %s", module_name)
