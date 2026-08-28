"""
PostToolUse hook — automatically updates the active metrics JSON when key BA output files are written
or when Jira/Confluence publish tools fire.

Reads tool name and input/result from environment variables set by Claude Code hooks:
  CLAUDE_TOOL_NAME, CLAUDE_TOOL_INPUT (JSON), CLAUDE_TOOL_RESULT (JSON)

Re-entrancy guard: exits immediately if the written path is inside output/metrics/ to prevent loops.
"""

import json
import os
import re
import sys
import glob
from datetime import datetime, timezone


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_metrics(path):
    with open(path) as f:
        return json.load(f)


def save_metrics(path, m):
    with open(path, "w") as f:
        json.dump(m, f, indent=2)


def find_active_metrics(req_id=None):
    """Find the in_progress metrics file, optionally matching req_id."""
    files = sorted(glob.glob("output/metrics/*.json"))
    candidates = []
    for fp in files:
        try:
            m = load_metrics(fp)
        except Exception:
            continue
        if m.get("status") == "in_progress":
            if req_id and m.get("feature_requirement_id") == req_id:
                return fp, m
            candidates.append((fp, m))
    if candidates:
        return candidates[-1]  # most recently modified
    return None, None


def extract_req_id_from_path(path):
    """Extract NEW-XXXX from a spec filename."""
    match = re.search(r"functional_spec_([^_/\\]+)_", path)
    return match.group(1) if match else None


def parse_validation_report(path):
    """Parse output/validation/validation-report.md and count structural vs content violations."""
    structural_rules = {3, 4, 5, 8}
    content_rules = {1, 2, 6, 7}
    struct_blockers = struct_warnings = 0
    content_blockers = content_warnings = content_infos = 0

    try:
        with open(path) as f:
            text = f.read()
    except FileNotFoundError:
        return None

    # Find each flag block and extract Rule number + Severity
    rule_pattern = re.compile(r'\*\*Rule:\*\*\s+Rule\s+(\d+)', re.IGNORECASE)
    sev_pattern = re.compile(r'\*\*Severity:\*\*\s+(BLOCKER|WARNING|INFO)', re.IGNORECASE)

    flags = re.split(r'###\s+FLAG-\d+', text)[1:]  # split on each FLAG block
    for block in flags:
        rule_match = rule_pattern.search(block)
        sev_match = sev_pattern.search(block)
        if not rule_match or not sev_match:
            continue
        rule_num = int(rule_match.group(1))
        severity = sev_match.group(1).upper()

        if rule_num in structural_rules:
            if severity == "BLOCKER":
                struct_blockers += 1
            elif severity == "WARNING":
                struct_warnings += 1
        elif rule_num in content_rules:
            if severity == "BLOCKER":
                content_blockers += 1
            elif severity == "WARNING":
                content_warnings += 1
            elif severity == "INFO":
                content_infos += 1

    return {
        "structural": {"blockers": struct_blockers, "warnings": struct_warnings},
        "content": {"blockers": content_blockers, "warnings": content_warnings, "infos": content_infos},
    }


def classify_story_file(path):
    """Return 'cr' or 'us' based on filename pattern."""
    name = os.path.basename(path).lower()
    if "-cr-" in name or name.startswith("cr-"):
        return "cr"
    if "-us-" in name or name.startswith("us-"):
        return "us"
    return "unknown"


def main():
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input_raw = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    tool_result_raw = os.environ.get("CLAUDE_TOOL_RESULT", "{}")

    try:
        tool_input = json.loads(tool_input_raw)
    except Exception:
        tool_input = {}
    try:
        tool_result = json.loads(tool_result_raw)
    except Exception:
        tool_result = {}

    # --- Write tool ---
    if tool_name == "Write":
        written_path = tool_input.get("file_path", "")

        # Re-entrancy guard — never update metrics when writing metrics files
        if "output/metrics" in written_path.replace("\\", "/"):
            sys.exit(0)

        # --- Spec file written ---
        if re.search(r"output/specs/functional_spec_.+\.html", written_path):
            req_id = extract_req_id_from_path(written_path)
            metrics_path, m = find_active_metrics(req_id)
            if not m:
                sys.exit(0)
            spec = m["phases"]["spec"]
            ts = now_iso()
            if not spec.get("started_at"):
                spec["started_at"] = ts
            spec["completed_at"] = ts
            spec["output_file"] = written_path
            if spec.get("started_at"):
                try:
                    start = datetime.fromisoformat(spec["started_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    spec["duration_minutes"] = round((end - start).total_seconds() / 60, 1)
                except Exception:
                    pass
            if req_id:
                m["feature_requirement_id"] = req_id
            save_metrics(metrics_path, m)
            print(f"[metrics] spec recorded: {written_path}")

        # --- Story file written ---
        elif re.search(r"output/stories/.+\.md", written_path):
            metrics_path, m = find_active_metrics()
            if not m:
                sys.exit(0)
            stories = m["phases"]["stories"]
            ts = now_iso()
            if not stories.get("started_at"):
                stories["started_at"] = ts
            stories["completed_at"] = ts
            # Append to output_files if not already listed
            if written_path not in stories.get("output_files", []):
                stories.setdefault("output_files", []).append(written_path)
            # Update CR / US counts from file list
            all_files = stories["output_files"]
            stories["cr_count"] = sum(1 for p in all_files if classify_story_file(p) == "cr")
            stories["us_count"] = sum(1 for p in all_files if classify_story_file(p) == "us")
            save_metrics(metrics_path, m)
            print(f"[metrics] story recorded: {written_path}")

        # --- Validation report written ---
        elif re.search(r"output/validation/validation-report\.md", written_path):
            metrics_path, m = find_active_metrics()
            if not m:
                sys.exit(0)
            counts = parse_validation_report(written_path)
            if counts:
                ts = now_iso()
                run = {
                    "started_at": ts,
                    "completed_at": ts,
                    "structural_violations": counts["structural"],
                    "content_violations": counts["content"],
                }
                m["phases"]["validation"].setdefault("runs", []).append(run)
                save_metrics(metrics_path, m)
                print(f"[metrics] validation run recorded from {written_path}")

    # --- Jira publish ---
    elif "jira_update_issue" in tool_name:
        ticket_key = tool_input.get("issue_key") or tool_input.get("issueKey", "")
        if not ticket_key:
            sys.exit(0)
        metrics_path, m = find_active_metrics()
        if not m:
            sys.exit(0)
        pub = m["phases"]["publish"]
        if ticket_key not in pub.get("jira_tickets", []):
            pub.setdefault("jira_tickets", []).append(ticket_key)
        if not pub.get("started_at"):
            pub["started_at"] = now_iso()
        save_metrics(metrics_path, m)
        print(f"[metrics] jira ticket recorded: {ticket_key}")

    # --- Confluence publish ---
    elif "confluence_update_page" in tool_name:
        page_url = (
            tool_result.get("url")
            or tool_result.get("_links", {}).get("base", "")
            or tool_input.get("pageId", "")
        )
        metrics_path, m = find_active_metrics()
        if not m:
            sys.exit(0)
        pub = m["phases"]["publish"]
        pub["confluence_page"] = page_url or pub.get("confluence_page")
        if not pub.get("started_at"):
            pub["started_at"] = now_iso()
        save_metrics(metrics_path, m)
        print(f"[metrics] confluence page recorded: {page_url}")


if __name__ == "__main__":
    main()
