#!/usr/bin/env python3
"""
Post-write coverage report hook for the MSC BA Agent.
Runs after confluence_update_page tool call completes.
Reads tool input and result from stdin and prints a summary to the terminal.
"""

import sys
import json
import re

SA_SECTIONS = [
    "Solution Overview",
    "Involved Interfaces",
    "Sequence Diagrams",
    "Monitoring and Alerting Guidelines",
]


def count_pattern(html: str, pattern: str) -> int:
    return len(re.findall(pattern, html))


def check_sa_sections(html: str) -> list[str]:
    """Check that all four SA-owned sections are still present in the saved page."""
    missing = []
    for section in SA_SECTIONS:
        if section.lower() not in html.lower():
            missing.append(section)
    return missing


def extract_tbc_count(html: str) -> int:
    return len(re.findall(r"\[TO BE CONFIRMED\]", html, re.IGNORECASE))


def extract_page_url(tool_result) -> str:
    if isinstance(tool_result, dict):
        return tool_result.get("url", tool_result.get("_links", {}).get("webui", ""))
    if isinstance(tool_result, str):
        match = re.search(r"https?://[^\s]+", tool_result)
        if match:
            return match.group(0)
    return ""


def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    tool_result = hook_input.get("tool_result", {})

    if tool_name != "confluence_update_page":
        sys.exit(0)

    html_content = tool_input.get("content", "") or tool_input.get("body", "")
    page_title = tool_input.get("title", "Unknown page")
    page_url = extract_page_url(tool_result)

    if not html_content:
        sys.exit(0)

    br_count = count_pattern(html_content, r"BR-\d{3}")
    uc_count = count_pattern(html_content, r"UC-\d{3}")
    nfr_count = count_pattern(html_content, r"NFR-\d{3}")
    test_scenario_count = count_pattern(html_content, r"UC-\d{3}") - uc_count + count_pattern(html_content, r"<tr>") - 1
    tbc_count = extract_tbc_count(html_content)
    missing_sa = check_sa_sections(html_content)

    print("\n📋 BA POST-WRITE REPORT", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print(f"Page:   {page_title}", file=sys.stderr)
    if page_url:
        print(f"URL:    {page_url}", file=sys.stderr)
    print(f"Status: Saved as DRAFT — must be published manually in Confluence", file=sys.stderr)

    print(f"\nContent written:", file=sys.stderr)
    print(f"  Business Requirements : {br_count}", file=sys.stderr)
    print(f"  Use Cases             : {uc_count}", file=sys.stderr)
    print(f"  NFRs                  : {nfr_count}", file=sys.stderr)

    if tbc_count:
        print(f"\n⚠️  {tbc_count} [TO BE CONFIRMED] field(s) remain — follow up before publishing", file=sys.stderr)
    else:
        print(f"\n✅ No [TO BE CONFIRMED] fields remaining", file=sys.stderr)

    if missing_sa:
        print(f"\n🚨 SA SECTION INTEGRITY WARNING — the following protected sections are missing from the saved page:", file=sys.stderr)
        for section in missing_sa:
            print(f"  • {section}", file=sys.stderr)
        print("  → These sections are SA-owned and must never be removed.", file=sys.stderr)
        print("  → Check the page in Confluence immediately before publishing.", file=sys.stderr)
    else:
        print(f"✅ All 4 SA-owned sections intact (Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines)", file=sys.stderr)

    print(f"\n→ Next: review the draft in Confluence, then publish manually.", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
