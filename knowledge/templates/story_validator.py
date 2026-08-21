#!/usr/bin/env python3
"""
story_validator.py — validates a BA story Markdown file against the required template structure.

Usage:
    python3 story_validator.py --type=cr  <story_file.md>
    python3 story_validator.py --type=us  <story_file.md>

Exit codes:
    0 — valid (no violations)
    1 — invalid (violations found)

Output:
    JSON array of violations, or the string "OK"
"""

import sys
import json
import re
import argparse
from pathlib import Path


CR_REQUIRED_SECTIONS = [
    "Summary",
    "Change Scope",
    "Interfaces Affected",
    "Rationale",
    "Resources",
    "Acceptance Criteria",
]

US_REQUIRED_SECTIONS = [
    "Summary",
    "User Story Statement",
    "Story Details",
    "Use Cases",
    "Functionality",
    "Acceptance Criteria",
    "Documentation",
    "Open Questions",
]

BDD_PATTERN = re.compile(r"\bGiven\b.+\bWhen\b.+\bThen\b", re.IGNORECASE | re.DOTALL)
INTERFACE_FORMAT_PATTERN = re.compile(r"\bINT\d{3,}\b", re.IGNORECASE)
VAGUE_LANGUAGE_PATTERN = re.compile(
    r"\b(works correctly|is fast|runs quickly|data is saved|system responds|good performance|is correct)\b",
    re.IGNORECASE,
)
INLINE_STYLE_PATTERN = re.compile(r'\bstyle\s*=\s*["\']', re.IGNORECASE)


def count_words(text: str) -> int:
    return len(re.sub(r"\s+", " ", text.strip()).split())


def extract_heading_value(md: str, heading: str) -> str | None:
    """Return the text on the same line as ## Heading, or None if not found."""
    pattern = re.compile(r"^#{1,3}\s+" + re.escape(heading) + r"\s*:?\s*(.*)$", re.MULTILINE | re.IGNORECASE)
    m = pattern.search(md)
    if m:
        return m.group(1).strip()
    # Also check for heading on its own line (value on next non-empty line)
    pattern2 = re.compile(r"^#{1,3}\s+" + re.escape(heading) + r"\s*$", re.MULTILINE | re.IGNORECASE)
    m2 = pattern2.search(md)
    if m2:
        rest = md[m2.end():].lstrip("\n\r ")
        first_line = rest.split("\n")[0].strip()
        return first_line if first_line else None
    return None


def section_exists(md: str, section: str) -> bool:
    pattern = re.compile(r"^#{1,3}\s+" + re.escape(section), re.MULTILINE | re.IGNORECASE)
    return bool(pattern.search(md))


def get_section_content(md: str, section: str) -> str:
    pattern = re.compile(
        r"^#{1,3}\s+" + re.escape(section) + r".*?\n(.*?)(?=^#{1,3}\s|\Z)",
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(md)
    if m:
        return m.group(1).strip()
    return ""


def validate_cr(md: str, file_path: str) -> list[dict]:
    violations = []

    # Rule 12a — Required sections present
    for section in CR_REQUIRED_SECTIONS:
        if not section_exists(md, section):
            violations.append({
                "rule": "Rule 12 — CR template compliance",
                "severity": "BLOCKER",
                "file": file_path,
                "section": section,
                "issue": f"Required CR section '## {section}' is missing.",
                "fix": f"Add a '## {section}' heading with appropriate content.",
            })

    # Rule 12b — Summary ≤ 10 words
    summary = extract_heading_value(md, "Summary")
    if summary and count_words(summary) > 10:
        violations.append({
            "rule": "Rule 12 — CR template compliance",
            "severity": "BLOCKER",
            "file": file_path,
            "section": "Summary",
            "issue": f"CR Summary is {count_words(summary)} words. Maximum is 10 words.",
            "fix": "Shorten the Summary to 10 words or fewer.",
        })

    # Rule 12c — Acceptance Criteria use BDD format with at least 2 scenarios
    ac_content = get_section_content(md, "Acceptance Criteria")
    if ac_content:
        if not BDD_PATTERN.search(ac_content):
            violations.append({
                "rule": "Rule 12 — CR template compliance",
                "severity": "BLOCKER",
                "file": file_path,
                "section": "Acceptance Criteria",
                "issue": "Acceptance Criteria do not use Given/When/Then format.",
                "fix": "Rewrite each criterion as: Given [precondition] / When [action] / Then [expected outcome].",
            })
        else:
            given_count = len(re.findall(r"\bGiven\b", ac_content, re.IGNORECASE))
            if given_count < 2:
                violations.append({
                    "rule": "Rule 12 — CR template compliance",
                    "severity": "BLOCKER",
                    "file": file_path,
                    "section": "Acceptance Criteria",
                    "issue": "Acceptance Criteria has only 1 BDD scenario. At least 2 required (happy path + 1 error/alt).",
                    "fix": "Add a second Given/When/Then block for an error scenario or alternative path.",
                })

    # Rule 12d — Change Scope names a specific endpoint/field (not vague)
    scope_content = get_section_content(md, "Change Scope")
    if scope_content and len(scope_content) < 20:
        violations.append({
            "rule": "Rule 12 — CR template compliance",
            "severity": "BLOCKER",
            "file": file_path,
            "section": "Change Scope",
            "issue": "Change Scope is too vague or too short. It must name a specific endpoint, field, or behaviour.",
            "fix": "Specify the exact endpoint, field, or method that is changing.",
        })

    # Rule 12e — No inline styles
    if INLINE_STYLE_PATTERN.search(md):
        violations.append({
            "rule": "Rule 12 — CR template compliance",
            "severity": "BLOCKER",
            "file": file_path,
            "section": "Entire document",
            "issue": "The story contains inline style= attributes. Plain Markdown only.",
            "fix": "Remove all inline style= attributes.",
        })

    return violations


def validate_us(md: str, file_path: str) -> list[dict]:
    violations = []

    # Rule 13a — Required sections present
    for section in US_REQUIRED_SECTIONS:
        if not section_exists(md, section):
            violations.append({
                "rule": "Rule 13 — User Story template compliance",
                "severity": "BLOCKER",
                "file": file_path,
                "section": section,
                "issue": f"Required User Story section '## {section}' is missing.",
                "fix": f"Add a '## {section}' heading with appropriate content.",
            })

    # Rule 13b — Summary ≤ 12 words
    summary = extract_heading_value(md, "Summary")
    if summary and count_words(summary) > 12:
        violations.append({
            "rule": "Rule 13 — User Story template compliance",
            "severity": "BLOCKER",
            "file": file_path,
            "section": "Summary",
            "issue": f"User Story Summary is {count_words(summary)} words. Maximum is 12 words.",
            "fix": "Shorten the Summary to 12 words or fewer.",
        })

    # Rule 13c — Interface Name format INT### Name
    interface_line = extract_heading_value(md, "Interface Name") or get_section_content(md, "Story Details")
    if interface_line and "INT" in interface_line.upper():
        if not INTERFACE_FORMAT_PATTERN.search(interface_line):
            violations.append({
                "rule": "Rule 13 — User Story template compliance",
                "severity": "BLOCKER",
                "file": file_path,
                "section": "Story Details / Interface Name",
                "issue": "Interface Name does not follow the format 'INT### Name' (e.g. 'INT118 Web User Deactivation').",
                "fix": "Use the format: INT[3-digit number] [Interface Name].",
            })

    # Rule 13d — Functionality has required subsections
    func_content = get_section_content(md, "Functionality")
    if func_content:
        for subsection in ["Authentication", "Happy Path", "Alternative Paths", "Error Scenarios"]:
            if subsection.lower() not in func_content.lower():
                violations.append({
                    "rule": "Rule 13 — User Story template compliance",
                    "severity": "BLOCKER",
                    "file": file_path,
                    "section": "Functionality",
                    "issue": f"Functionality section is missing the '{subsection}' subsection.",
                    "fix": f"Add a '{subsection}:' subsection inside Functionality.",
                })

    # Rule 13e — Acceptance Criteria use BDD format, at least 3 scenarios
    ac_content = get_section_content(md, "Acceptance Criteria")
    if ac_content:
        if not BDD_PATTERN.search(ac_content):
            violations.append({
                "rule": "Rule 13 — User Story template compliance",
                "severity": "BLOCKER",
                "file": file_path,
                "section": "Acceptance Criteria",
                "issue": "Acceptance Criteria do not use Given/When/Then format.",
                "fix": "Rewrite each criterion as: Given [precondition] / When [action] / Then [expected outcome].",
            })
        else:
            given_count = len(re.findall(r"\bGiven\b", ac_content, re.IGNORECASE))
            if given_count < 3:
                violations.append({
                    "rule": "Rule 13 — User Story template compliance",
                    "severity": "BLOCKER",
                    "file": file_path,
                    "section": "Acceptance Criteria",
                    "issue": f"Acceptance Criteria has {given_count} BDD scenario(s). At least 3 required (happy path, alternative, error).",
                    "fix": "Add BDD scenarios for: happy path, at least one alternative path, and at least one error scenario.",
                })

    # Rule 13f — No inline styles
    if INLINE_STYLE_PATTERN.search(md):
        violations.append({
            "rule": "Rule 13 — User Story template compliance",
            "severity": "BLOCKER",
            "file": file_path,
            "section": "Entire document",
            "issue": "The story contains inline style= attributes. Plain Markdown only.",
            "fix": "Remove all inline style= attributes.",
        })

    # Rule 14 — Structure consistency
    # Check for vague language in acceptance criteria
    if ac_content and VAGUE_LANGUAGE_PATTERN.search(ac_content):
        violations.append({
            "rule": "Rule 14 — Story structure consistency",
            "severity": "BLOCKER",
            "file": file_path,
            "section": "Acceptance Criteria",
            "issue": "Acceptance Criteria contains vague language (e.g. 'works correctly', 'is fast', 'data is saved').",
            "fix": "Replace vague phrases with specific, measurable outcomes (e.g. HTTP 200 returned with field X populated).",
        })

    # Check for empty required fields
    critical_fields = ["Summary", "User Story Statement"]
    for field in critical_fields:
        content = extract_heading_value(md, field) or get_section_content(md, field)
        if not content or len(content.strip()) < 10:
            violations.append({
                "rule": "Rule 14 — Story structure consistency",
                "severity": "BLOCKER",
                "file": file_path,
                "section": field,
                "issue": f"Required field '{field}' is empty or too short.",
                "fix": f"Populate '{field}' with substantive content or mark it [TO BE CONFIRMED].",
            })

    return violations


def main():
    parser = argparse.ArgumentParser(description="Validate a BA story Markdown file.")
    parser.add_argument("--type", choices=["cr", "us"], required=True, help="Story type: cr or us")
    parser.add_argument("file", help="Path to the Markdown story file")
    args = parser.parse_args()

    file_path = args.file
    if not Path(file_path).exists():
        print(json.dumps([{
            "rule": "File not found",
            "severity": "BLOCKER",
            "file": file_path,
            "section": "—",
            "issue": f"File not found: {file_path}",
            "fix": "Check the file path and try again.",
        }]))
        sys.exit(1)

    md = Path(file_path).read_text(encoding="utf-8", errors="replace")

    if args.type == "cr":
        violations = validate_cr(md, file_path)
    else:
        violations = validate_us(md, file_path)

    if not violations:
        print("OK")
        sys.exit(0)
    else:
        print(json.dumps(violations, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
