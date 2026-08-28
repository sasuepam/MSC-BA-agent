#!/usr/bin/env python3
"""
Pre-write validation hook for the MSC BA Agent.
Runs before confluence_update_page tool calls.
Reads tool input from stdin and checks for BA spec quality issues.
Exits with code 2 (block) if critical issues found, 0 (allow) if clean.
"""

import sys
import json
import re

REQUIRED_SECTIONS = [
    "Document History",
    "Feature Summary",
    "Business Requirements",
    "Use Cases",
    "Test Scenarios",
]


def check_tbc_fields(html: str) -> list[str]:
    """Block if any [TO BE CONFIRMED] placeholders remain."""
    issues = []
    count = len(re.findall(r"\[TO BE CONFIRMED\]", html, re.IGNORECASE))
    if count:
        issues.append(
            f"{count} unresolved [TO BE CONFIRMED] field(s) found — resolve all placeholders before publishing to Confluence"
        )
    return issues


def check_required_sections(html: str) -> list[str]:
    """Warn if any required BA sections are missing."""
    issues = []
    for section in REQUIRED_SECTIONS:
        if section.lower() not in html.lower():
            issues.append(f"Required section appears to be missing: '{section}'")
    return issues


def check_business_requirements(html: str) -> list[str]:
    """Warn if no Business Requirements rows are found."""
    issues = []
    if not re.search(r"BR-\d{3}", html):
        issues.append("No Business Requirements found (expected pattern BR-001, BR-002, …) — section may be empty")
    return issues


def check_use_cases(html: str) -> list[str]:
    """Warn if no Use Case rows are found."""
    issues = []
    if not re.search(r"UC-\d{3}", html):
        issues.append("No Use Cases found (expected pattern UC-001, UC-002, …) — section may be empty")
    return issues


def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name != "confluence_update_page":
        sys.exit(0)

    html_content = tool_input.get("content", "") or tool_input.get("body", "")
    if not html_content:
        sys.exit(0)

    critical_issues = check_tbc_fields(html_content)
    warnings = (
        check_required_sections(html_content)
        + check_business_requirements(html_content)
        + check_use_cases(html_content)
    )

    if critical_issues or warnings:
        print("\n🔍 BA PRE-WRITE VALIDATION", file=sys.stderr)
        print("=" * 50, file=sys.stderr)

        if critical_issues:
            print(f"\n🚨 CRITICAL ({len(critical_issues)}) — write blocked:", file=sys.stderr)
            for issue in critical_issues:
                print(f"  • {issue}", file=sys.stderr)

        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}) — please review before publishing:", file=sys.stderr)
            for warning in warnings:
                print(f"  • {warning}", file=sys.stderr)

        if critical_issues:
            print("\n❌ Write blocked. Resolve all [TO BE CONFIRMED] fields first.", file=sys.stderr)
            sys.exit(2)
        else:
            print("\n✅ Warnings noted. Write allowed — review before publishing.", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
