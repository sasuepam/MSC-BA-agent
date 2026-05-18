#!/usr/bin/env python3
"""
Pre-write validation hook.
Runs before confluence_create_page or confluence_update_page tool calls.
Reads the HTML content from stdin (passed by Claude Code hook) and checks for quality issues.
Exits with code 2 (block) if critical issues found, 0 (allow) if clean.

PRODUCTION WRITE LOCK:
Any write to production Confluence (instance=production or space_key=DTP) is blocked
unless the HTML content contains the marker: <!-- PROD-CONFIRMED -->
This marker is only added by Claude after the designer types the exact confirmation phrase.
"""

import sys
import json
import re

# Production identifiers — writes to these are blocked without PROD-CONFIRMED marker
PRODUCTION_INSTANCES = {"production", "prod"}
PRODUCTION_SPACE_KEYS = {"DTP"}
SANDBOX_SPACE_KEY = "~5c599247178bcb38b9594eea"
PROD_CONFIRMATION_MARKER = "<!-- PROD-CONFIRMED -->"

# Blocked headers — never add these unless explicitly in IA
BLOCKED_HEADERS = [
    "MSC-Agency-Id",
    "MSC-Agent-Id",
    "MSC-Booking-Channel",
    "MSC-Booking-Contact-Name",
    "MSC-Market-Code",
    "MSC-Office-Code",
    "MSC-Channel-Id",
    "MSC-Locale",
    "MSC-Booking-Contact-Email",
]

# Known hallucinated field names
HALLUCINATED_FIELDS = [
    "promotionalCode",
    "promoCode",
]

# Correct parent IDs for sandbox pages
CORRECT_PARENT_IDS = {
    "MUL": "688129",
    "EAPI": "917505",
    "PAPI": "786433",
    "SAPI": "851969",
}


def check_blocked_headers(html: str) -> list[str]:
    """Check for headers that should not be in the page."""
    issues = []
    for header in BLOCKED_HEADERS:
        if header in html:
            issues.append(f"BLOCKED HEADER found: {header} — should not be in this page unless explicitly in IA")
    return issues


def check_hallucinated_fields(html: str) -> list[str]:
    """Check for known false-positive field names."""
    issues = []
    for field in HALLUCINATED_FIELDS:
        # Look for field in table cells (td tags)
        pattern = f"<td[^>]*>{re.escape(field)}</td>"
        if re.search(pattern, html):
            issues.append(f"POSSIBLE HALLUCINATION: field '{field}' found in table — verify this is in the IA (common trap: 'promotionalCode' should usually be 'couponCode')")
    return issues


def check_empty_sections(html: str) -> list[str]:
    """Check that H1 sections have content after them."""
    issues = []
    # Find H1 tags followed immediately by another H1 (empty section)
    empty_section_pattern = r"<h1>[^<]+</h1>\s*<h1>"
    matches = re.findall(r"<h1>([^<]+)</h1>\s*<h1>", html)
    for match in matches:
        issues.append(f"WARNING: Section '{match}' appears to be empty")
    return issues


def check_row_count(html: str) -> list[str]:
    """Basic sanity check on table row count."""
    issues = []
    tr_count = html.count("<tr>")
    if tr_count < 5:
        issues.append(f"WARNING: Very few table rows ({tr_count}) — page may be incomplete")
    return issues


def check_production_write(tool_input: dict, html_content: str) -> list[str]:
    """
    HARD BLOCK: Prevent any write to production without explicit designer confirmation.
    Production is identified by instance=production/prod OR space_key=DTP.
    The only bypass is the PROD-CONFIRMED marker in the HTML content,
    which Claude adds only after the designer types the exact confirmation phrase.
    """
    issues = []

    instance = tool_input.get("instance", "").lower().strip()
    space_key = tool_input.get("space_key", "").strip()

    is_production = (
        instance in PRODUCTION_INSTANCES
        or space_key in PRODUCTION_SPACE_KEYS
    )

    if is_production:
        has_confirmation = PROD_CONFIRMATION_MARKER in html_content
        if not has_confirmation:
            issues.append(
                f"PRODUCTION WRITE BLOCKED — instance='{instance}', space_key='{space_key}'. "
                f"The designer must type 'YES PUBLISH TO PRODUCTION' to confirm, and the "
                f"confirmation marker '{PROD_CONFIRMATION_MARKER}' must be present in the content. "
                f"Default to sandbox (instance=sandbox, space_key={SANDBOX_SPACE_KEY}) instead."
            )

    return issues


def main():
    # Claude Code hooks pass tool input as JSON on stdin
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        # If we can't read input, don't block
        sys.exit(0)

    # Extract HTML content from tool parameters
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name not in ("confluence_create_page", "confluence_update_page"):
        sys.exit(0)

    html_content = tool_input.get("content", "")
    if not html_content:
        sys.exit(0)

    # Run checks — production lock first (hardest block)
    critical_issues = []
    warnings = []

    production_issues = check_production_write(tool_input, html_content)
    if production_issues:
        print("\n🔒 PRODUCTION WRITE LOCK", file=sys.stderr)
        print("=" * 50, file=sys.stderr)
        print("\n🚨 BLOCKED — This write targets PRODUCTION:", file=sys.stderr)
        for issue in production_issues:
            print(f"  • {issue}", file=sys.stderr)
        print("\n❌ Write to production is BLOCKED.", file=sys.stderr)
        print("   Required steps:", file=sys.stderr)
        print("   1. Designer must explicitly say 'publish to production'", file=sys.stderr)
        print("   2. You must show the full page content for review", file=sys.stderr)
        print("   3. Designer must type exactly: YES PUBLISH TO PRODUCTION", file=sys.stderr)
        print("   4. Add <!-- PROD-CONFIRMED --> at top of HTML content", file=sys.stderr)
        print("   5. Then retry the tool call", file=sys.stderr)
        print("\n   If this was unintentional, use instance=sandbox instead.", file=sys.stderr)
        sys.exit(2)

    critical_issues.extend(check_blocked_headers(html_content))
    warnings.extend(check_hallucinated_fields(html_content))
    warnings.extend(check_empty_sections(html_content))
    warnings.extend(check_row_count(html_content))

    # Output results
    if critical_issues or warnings:
        print("\n🔍 PRE-WRITE VALIDATION REPORT", file=sys.stderr)
        print("=" * 50, file=sys.stderr)

        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical_issues)}) — write blocked:", file=sys.stderr)
            for issue in critical_issues:
                print(f"  • {issue}", file=sys.stderr)

        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}) — please review:", file=sys.stderr)
            for warning in warnings:
                print(f"  • {warning}", file=sys.stderr)

        if critical_issues:
            print("\n❌ Write blocked. Fix critical issues first.", file=sys.stderr)
            print("To override: confirm the blocked header IS in the IA for this interface, then run /update to proceed.", file=sys.stderr)
            sys.exit(2)
        else:
            print("\n✅ Warnings noted. Write allowed — please review.", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
