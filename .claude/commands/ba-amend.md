Read the validation report at `C:\Users\[your_user]\MSC- Mule BA Agent\output\validation\validation-report.md`.

Work through every FLAG in the report one at a time, in severity order (BLOCKERs first, then WARNINGs, then INFOs).

For each flag, present it to the user in this format and wait for their response before moving to the next:

---

**FLAG-[NNN] — [Rule name] · [Severity]**

- **File:** [filename]
- **Section:** [section]
- **Issue:** [issue description]
- **Suggested fix:** [suggested fix]

How would you like to handle this?
1. **Accept fix** — apply the suggested fix automatically
2. **Edit manually** — you provide the replacement text and I apply it
3. **Skip** — leave this flag unresolved for now

---

## Handling each response

### 1 — Accept fix
Apply the suggested fix directly to the relevant file in `output/specs/` or `output/stories/` using the Write or Edit tool.
Confirm: "✓ FLAG-[NNN] applied to [filename]."
Move to the next flag.

### 2 — Edit manually
Ask the user: "Please provide the replacement text."
Wait for their input, then apply exactly what they provide to the relevant file.
Confirm: "✓ FLAG-[NNN] updated in [filename] with your text."
Move to the next flag.

### 3 — Skip
Record this flag as skipped.
Move to the next flag without making any changes.

---

## Editing rules

- Make the minimum change needed to resolve the flag — do not rewrite surrounding content.
- Never remove content from a protected Confluence section (Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines) even if a flag points to one of them — skip those automatically and inform the user.
- Preserve all formatting, table structure, and HTML validity when editing spec files.
- Preserve all Markdown structure when editing story files.

---

## After all flags are processed

Print a final summary:

```
## Amendment Summary

| Status  | Count |
|---------|-------|
| Applied | [n]   |
| Edited  | [n]   |
| Skipped | [n]   |

Files modified:
- [list each file that was changed]

Skipped flags:
- [FLAG-NNN — reason skipped or user chose to skip]
```

Then tell the user: "Run /ba-amend again or re-run the ba-validator agent to check remaining issues."
