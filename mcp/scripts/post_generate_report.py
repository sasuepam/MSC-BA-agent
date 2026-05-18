#!/usr/bin/env python3
"""
Post-write coverage report hook.
Runs after confluence_create_page tool call completes.
Reads the tool result (page URL) and tool input (HTML content) from stdin.
Outputs a quick coverage summary to terminal.
"""

import sys
import json
import re


def count_table_rows(html: str, section_hint: str = "") -> int:
    """Count <tr> elements in HTML, excluding header rows."""
    rows = html.count("<tr>")
    # Subtract header rows (rows with <th> tags)
    header_rows = len(re.findall(r"<tr>\s*<th", html))
    return max(0, rows - header_rows)


def extract_page_title(html: str) -> str:
    """Try to extract a meaningful title from the HTML."""
    match = re.search(r"<h1>([^<]+)</h1>", html)
    return match.group(1) if match else "Unknown page"


def check_blocked_headers(html: str) -> list[str]:
    """Check for headers that should not be in the page."""
    BLOCKED_HEADERS = [
        "MSC-Agency-Id", "MSC-Agent-Id", "MSC-Booking-Channel",
        "MSC-Booking-Contact-Name", "MSC-Market-Code", "MSC-Office-Code",
    ]
    found = []
    for header in BLOCKED_HEADERS:
        if header in html:
            found.append(header)
    return found


def check_required_sections(html: str, page_type: str = "") -> list[str]:
    """Check for required sections based on page type."""
    missing = []

    if "MUL" in page_type.upper() or not page_type:
        required_sections = [
            "Purpose", "Scope", "Authentication", "Request", "Response", "Error"
        ]
        for section in required_sections:
            if section.lower() not in html.lower():
                missing.append(f"Section possibly missing: {section}")

    return missing


def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    tool_result = hook_input.get("tool_result", {})

    if tool_name != "confluence_create_page":
        sys.exit(0)

    html_content = tool_input.get("content", "")
    page_title = tool_input.get("title", "")

    if not html_content:
        sys.exit(0)

    # Extract page URL from result
    page_url = ""
    if isinstance(tool_result, dict):
        page_url = tool_result.get("url", tool_result.get("_links", {}).get("webui", ""))
    elif isinstance(tool_result, str):
        url_match = re.search(r"https?://[^\s]+", tool_result)
        if url_match:
            page_url = url_match.group(0)

    # Count rows
    total_rows = count_table_rows(html_content)

    # Check for blocked headers
    blocked = check_blocked_headers(html_content)

    # Detect page type from title
    page_type = ""
    for pt in ["MUL", "EAPI", "PAPI", "SAPI"]:
        if pt in page_title.upper():
            page_type = pt
            break

    # Count H2/H3 sections
    h2_count = len(re.findall(r"<h2>", html_content))
    h3_count = len(re.findall(r"<h3>", html_content))

    # Output report
    print("\n📊 POST-WRITE COVERAGE REPORT", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print(f"Page: {page_title}", file=sys.stderr)
    if page_url:
        print(f"URL:  {page_url}", file=sys.stderr)
    print(f"\nStats:", file=sys.stderr)
    print(f"  Table rows: {total_rows}", file=sys.stderr)
    print(f"  H2 sections: {h2_count}", file=sys.stderr)
    print(f"  H3 subsections: {h3_count}", file=sys.stderr)

    if blocked:
        print(f"\n⚠️  BLOCKED HEADERS FOUND (these should only be here if in IA):", file=sys.stderr)
        for h in blocked:
            print(f"  • {h}", file=sys.stderr)
        print("  → Run /validate to check against IA", file=sys.stderr)
    else:
        print(f"\n✅ No blocked headers detected", file=sys.stderr)

    if total_rows < 10:
        print(f"\n⚠️  Low row count ({total_rows}) — consider running /validate to check coverage", file=sys.stderr)
    else:
        print(f"✅ Row count looks reasonable — run /validate for full coverage check", file=sys.stderr)

    print(f"\n→ Next: /validate to cross-check against IA", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
