#!/usr/bin/env python3
"""
spec_validator.py — validates a functional spec HTML file against the required template structure.

Usage:
    python3 spec_validator.py <spec_file.html>

Exit codes:
    0 — valid (no violations)
    1 — invalid (violations found)

Output:
    JSON array of violations, or the string "OK"
"""

import sys
import json
import re
from pathlib import Path


REQUIRED_H2_SECTIONS = [
    "Document History",
    "Reference Documentation",
    "Feature Summary",
    "Business Requirements",
    "Use Cases",
    "Solution Overview",
    "Involved Interfaces",
    "Sequence Diagrams",
    "Non-Functional Requirements",
    "Monitoring and Alerting Guidelines",
    "Test Scenarios & Acceptance Criteria",
]

USE_CASES_REQUIRED_HEADERS = ["UC#", "PreCondition", "Actor", "Use Case", "Functionality Expected", "Open Questions"]
BR_USER_STORY_PATTERN = re.compile(r"As a .+ I want .+ so that", re.IGNORECASE)
NFR_REQUIRED_HEADERS = ["Requirement ID", "Interface", "Requirement Description", "Category", "Priority"]
TEST_SCENARIO_REQUIRED_HEADERS = ["Use Case", "Test Cases", "Acceptance Criteria", "Test Data"]
STYLE_BLOCK_PATTERN = re.compile(r"<style[\s>]", re.IGNORECASE)
INLINE_STYLE_PATTERN = re.compile(r'\bstyle\s*=\s*["\']', re.IGNORECASE)


def extract_h2_sections(html: str) -> list[str]:
    pattern = re.compile(r"<h2[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
    return [re.sub(r"<[^>]+>", "", m.group(1)).strip() for m in pattern.finditer(html)]


def extract_table_headers(html: str, section_start: int, section_end: int) -> list[str]:
    """Extract all <th> text values from the first table found in the section slice."""
    snippet = html[section_start:section_end]
    th_pattern = re.compile(r"<th[^>]*>(.*?)</th>", re.IGNORECASE | re.DOTALL)
    return [re.sub(r"<[^>]+>", "", m.group(1)).strip() for m in th_pattern.finditer(snippet)]


def find_section_bounds(html: str, section_name: str) -> tuple[int, int]:
    """Return (start, end) character positions of the section's content."""
    pattern = re.compile(
        r"<h2[^>]*>" + re.escape(section_name) + r".*?</h2>(.*?)(?=<h2|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(html)
    if not m:
        return (-1, -1)
    return (m.start(1), m.end(1))


def check_sections_present(html: str) -> list[dict]:
    violations = []
    found = extract_h2_sections(html)
    # Normalise for comparison (strip special chars)
    found_normalised = [re.sub(r"[^a-z0-9 ]", "", s.lower()) for s in found]
    for required in REQUIRED_H2_SECTIONS:
        req_norm = re.sub(r"[^a-z0-9 ]", "", required.lower())
        if req_norm not in found_normalised:
            violations.append({
                "rule": "Rule 9 — Spec template structure compliance",
                "severity": "BLOCKER",
                "section": required,
                "issue": f"Required section <h2>{required}</h2> is missing from the spec.",
                "fix": f"Add the missing section heading and populate it or mark content [TO BE CONFIRMED].",
            })
    return violations


def check_use_cases_table(html: str) -> list[dict]:
    violations = []
    start, end = find_section_bounds(html, "Use Cases")
    if start == -1:
        return violations  # already caught by section check
    headers = extract_table_headers(html, start, end)
    if not headers:
        violations.append({
            "rule": "Rule 9 — Spec template structure compliance",
            "severity": "BLOCKER",
            "section": "Use Cases",
            "issue": "Use Cases section has no table.",
            "fix": "Add a table with columns: UC#, PreCondition, Actor/s, Use Case, Functionality Expected, Open Questions.",
        })
        return violations
    for required_col in USE_CASES_REQUIRED_HEADERS:
        req_norm = required_col.lower()
        if not any(req_norm in h.lower() for h in headers):
            violations.append({
                "rule": "Rule 9 — Spec template structure compliance",
                "severity": "BLOCKER",
                "section": "Use Cases",
                "issue": f"Use Cases table is missing the '{required_col}' column header.",
                "fix": f"Add a <th>{required_col}</th> column to the Use Cases table.",
            })
    return violations


def check_business_requirements_format(html: str) -> list[dict]:
    violations = []
    start, end = find_section_bounds(html, "Business Requirements")
    if start == -1:
        return violations
    snippet = html[start:end]
    # Find all <td> content (requirement statements)
    td_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
    cells = [re.sub(r"<[^>]+>", "", m.group(1)).strip() for m in td_pattern.finditer(snippet)]
    # The second column (Requirements) should contain user story format
    # Check cells that look like requirement statements (not IDs or descriptions)
    req_cells = [c for c in cells if len(c) > 20 and not c.startswith("BR-") and "as a" in c.lower()]
    non_compliant = [c for c in req_cells if not BR_USER_STORY_PATTERN.search(c)]
    if non_compliant:
        violations.append({
            "rule": "Rule 9 — Spec template structure compliance",
            "severity": "BLOCKER",
            "section": "Business Requirements",
            "issue": f"{len(non_compliant)} requirement(s) do not follow the user story format 'As a [actor] I want [action] so that [benefit]'.",
            "fix": "Rewrite each requirement using: 'As a [actor] I want to [action] so that [benefit]'.",
        })
    return violations


def check_nfr_table(html: str) -> list[dict]:
    violations = []
    start, end = find_section_bounds(html, "Non-Functional Requirements")
    if start == -1:
        return violations
    headers = extract_table_headers(html, start, end)
    if not headers:
        violations.append({
            "rule": "Rule 9 — Spec template structure compliance",
            "severity": "BLOCKER",
            "section": "Non-Functional Requirements",
            "issue": "NFR section has no table.",
            "fix": "Add a table with columns: Requirement ID, Interface, Requirement Description, Category, Priority.",
        })
        return violations
    for required_col in NFR_REQUIRED_HEADERS:
        if not any(required_col.lower() in h.lower() for h in headers):
            violations.append({
                "rule": "Rule 9 — Spec template structure compliance",
                "severity": "BLOCKER",
                "section": "Non-Functional Requirements",
                "issue": f"NFR table is missing the '{required_col}' column header.",
                "fix": f"Add a <th>{required_col}</th> column to the NFR table.",
            })
    return violations


def check_test_scenarios_table(html: str) -> list[dict]:
    violations = []
    start, end = find_section_bounds(html, "Test Scenarios & Acceptance Criteria")
    if start == -1:
        # Try alternate spelling
        start, end = find_section_bounds(html, "Test Scenarios")
    if start == -1:
        return violations
    headers = extract_table_headers(html, start, end)
    if not headers:
        violations.append({
            "rule": "Rule 9 — Spec template structure compliance",
            "severity": "BLOCKER",
            "section": "Test Scenarios & Acceptance Criteria",
            "issue": "Test Scenarios section has no table.",
            "fix": "Add a table with columns: Use Case, Test Cases, Acceptance Criteria, Test Data.",
        })
        return violations
    for required_col in TEST_SCENARIO_REQUIRED_HEADERS:
        if not any(required_col.lower() in h.lower() for h in headers):
            violations.append({
                "rule": "Rule 9 — Spec template structure compliance",
                "severity": "BLOCKER",
                "section": "Test Scenarios & Acceptance Criteria",
                "issue": f"Test Scenarios table is missing the '{required_col}' column header.",
                "fix": f"Add a <th>{required_col}</th> column to the Test Scenarios table.",
            })
    return violations


def check_no_inline_styles(html: str) -> list[dict]:
    violations = []
    if STYLE_BLOCK_PATTERN.search(html):
        violations.append({
            "rule": "Rule 9 — Spec template structure compliance",
            "severity": "BLOCKER",
            "section": "Entire document",
            "issue": "The spec contains a <style> block. Plain HTML only.",
            "fix": "Remove all <style> blocks from the document.",
        })
    if INLINE_STYLE_PATTERN.search(html):
        violations.append({
            "rule": "Rule 9 — Spec template structure compliance",
            "severity": "BLOCKER",
            "section": "Entire document",
            "issue": "The spec contains inline style= attributes. Plain HTML only.",
            "fix": "Remove all inline style= attributes from the document.",
        })
    return violations


def check_sa_sections_present(html: str) -> list[dict]:
    """Rule 10 — SA-owned sections must be present and not replaced with BA content."""
    violations = []
    sa_sections = ["Solution Overview", "Involved Interfaces", "Sequence Diagrams", "Monitoring and Alerting Guidelines"]
    for section in sa_sections:
        start, end = find_section_bounds(html, section)
        if start == -1:
            violations.append({
                "rule": "Rule 10 — Protected section preservation",
                "severity": "BLOCKER",
                "section": section,
                "issue": f"SA-owned section '{section}' is missing. It may have been accidentally removed.",
                "fix": f"Restore the '{section}' section with its original SA content or the placeholder 'Populated by Solution Architect.'",
            })
    return violations


def check_ba_sections_populated(html: str) -> list[dict]:
    """Rule 11 — Required BA sections must have substantive content."""
    violations = []
    critical_sections = {
        "Feature Summary": "BLOCKER",
        "Business Requirements": "BLOCKER",
        "Use Cases": "BLOCKER",
        "Test Scenarios & Acceptance Criteria": "BLOCKER",
        "Reference Documentation": "WARNING",
    }
    for section, severity in critical_sections.items():
        start, end = find_section_bounds(html, section)
        if start == -1:
            continue  # already caught by Rule 9
        content = re.sub(r"<[^>]+>", "", html[start:end]).strip()
        # Check if it's effectively empty or just the placeholder
        placeholder_only = re.sub(r"\[TO BE CONFIRMED\]", "", content).strip()
        if len(placeholder_only) < 30:
            violations.append({
                "rule": "Rule 11 — Required field population",
                "severity": severity,
                "section": section,
                "issue": f"Section '{section}' appears empty or contains only placeholders with no substantive content.",
                "fix": f"Populate '{section}' with content from the source materials, or mark specific fields [TO BE CONFIRMED] with a note explaining what is unknown.",
            })
    return violations


def validate(file_path: str) -> list[dict]:
    html = Path(file_path).read_text(encoding="utf-8", errors="replace")
    violations = []
    violations += check_sections_present(html)
    violations += check_use_cases_table(html)
    violations += check_business_requirements_format(html)
    violations += check_nfr_table(html)
    violations += check_test_scenarios_table(html)
    violations += check_no_inline_styles(html)
    violations += check_sa_sections_present(html)
    violations += check_ba_sections_populated(html)
    return violations


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 spec_validator.py <spec_file.html>", file=sys.stderr)
        sys.exit(2)

    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(json.dumps([{
            "rule": "File not found",
            "severity": "BLOCKER",
            "section": "—",
            "issue": f"File not found: {file_path}",
            "fix": "Check the file path and try again.",
        }]))
        sys.exit(1)

    violations = validate(file_path)

    if not violations:
        print("OK")
        sys.exit(0)
    else:
        print(json.dumps(violations, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
