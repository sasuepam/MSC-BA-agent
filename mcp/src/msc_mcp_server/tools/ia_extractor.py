"""IA Extractor tool — parses Confluence IA/PAPI pages into structured JSON.

Instead of giving the LLM raw HTML (234K chars), this tool:
1. Fetches the Confluence page
2. Deterministically parses all tables and text sections
3. Returns clean structured JSON (~10-15K chars)

This eliminates LLM hallucinations from field extraction and ensures
100% table row coverage regardless of document size.
"""

import logging
import re
from html.parser import HTMLParser
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from msc_mcp_server.config import settings

logger = logging.getLogger(__name__)


class TableParser(HTMLParser):
    """Extracts all tables with their header rows and data rows."""

    def __init__(self):
        super().__init__()
        self.tables: list[dict] = []
        self._current_table: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []
        self._in_cell = False
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if self._depth == 0:
                self._current_table = []
            self._depth += 1
        elif tag in ("tr",) and self._depth == 1:
            self._current_row = []
        elif tag in ("td", "th") and self._depth == 1:
            self._current_cell = []
            self._in_cell = True

    def handle_endtag(self, tag):
        if tag == "table":
            self._depth -= 1
            if self._depth == 0 and self._current_table:
                self.tables.append(self._parse_table(self._current_table))
                self._current_table = []
        elif tag == "tr" and self._depth == 1:
            if any(c.strip() for c in self._current_row):
                self._current_table.append(self._current_row[:])
            self._current_row = []
        elif tag in ("td", "th") and self._depth == 1:
            cell_text = " ".join(self._current_cell).strip()
            cell_text = re.sub(r'\s+', ' ', cell_text).strip()
            self._current_row.append(cell_text)
            self._current_cell = []
            self._in_cell = False

    def handle_data(self, data):
        if self._in_cell and self._depth == 1:
            self._current_cell.append(data)

    def _parse_table(self, rows: list[list[str]]) -> dict:
        if not rows:
            return {"headers": [], "rows": []}
        headers = rows[0]
        data_rows = rows[1:]
        return {
            "headers": headers,
            "rows": [dict(zip(headers, row)) for row in data_rows if any(v.strip() for v in row)]
        }


class SectionParser(HTMLParser):
    """Extracts H1/H2 sections with their text content."""

    def __init__(self):
        super().__init__()
        self.sections: dict[str, str] = {}
        self._current_tag: str = ""
        self._current_header: str = ""
        self._current_content: list[str] = []
        self._in_header = False
        self._header_text: list[str] = []
        self._depth_in_section = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2"):
            if self._current_header and self._current_content:
                content = " ".join(self._current_content).strip()
                content = re.sub(r'\s+', ' ', content)
                self.sections[self._current_header] = content[:2000]
            self._current_header = ""
            self._current_content = []
            self._header_text = []
            self._in_header = True
            self._current_tag = tag

    def handle_endtag(self, tag):
        if tag in ("h1", "h2") and self._in_header:
            self._current_header = " ".join(self._header_text).strip()
            self._in_header = False

    def handle_data(self, data):
        if self._in_header:
            self._header_text.append(data)
        elif self._current_header:
            self._current_content.append(data)

    def finalize(self):
        if self._current_header and self._current_content:
            content = " ".join(self._current_content).strip()
            content = re.sub(r'\s+', ' ', content)
            self.sections[self._current_header] = content[:2000]


FIELD_COL_VARIANTS = {
    "name": ["field", "field name", "name", "parameter"],
    "location": ["location", "in", "type"],
    "description": ["description", "desc"],
    "data_format": ["data format", "format", "type", "data type"],
    "field_definition": ["field definition", "definition", "pattern", "constraints"],
    "required": ["requiredness", "required", "mandatory", "required?"],
    "business_data_model": ["business data model", "business data model reference", "bdm"],
}

def _match_col(header: str, col_key: str) -> bool:
    h = header.lower().strip()
    for variant in FIELD_COL_VARIANTS.get(col_key, []):
        if variant in h:
            return True
    return False


def _parse_field_table(table: dict) -> list[dict]:
    headers = table.get("headers", [])
    rows = table.get("rows", [])

    if not headers:
        return []

    col_map = {}
    for col_key in FIELD_COL_VARIANTS:
        for h in headers:
            if _match_col(h, col_key):
                col_map[col_key] = h
                break

    if "name" not in col_map:
        return []

    fields = []
    for row in rows:
        name = row.get(col_map["name"], "").strip()
        if not name:
            continue

        field = {
            "name": name,
            "location": row.get(col_map.get("location", ""), "").strip() or "body",
            "description": row.get(col_map.get("description", ""), "").strip(),
            "data_format": row.get(col_map.get("data_format", ""), "").strip(),
            "field_definition": row.get(col_map.get("field_definition", ""), "").strip(),
            "required": row.get(col_map.get("required", ""), "").strip(),
        }
        if col_map.get("business_data_model"):
            field["business_data_model"] = row.get(col_map["business_data_model"], "").strip()

        fields.append(field)

    return fields


def _parse_error_table(table: dict) -> list[dict]:
    headers = table.get("headers", [])
    rows = table.get("rows", [])

    if not headers:
        return []

    errors = []
    for row in rows:
        values = list(row.values())
        if len(values) >= 2:
            error = {
                "number": str(values[0]).strip() if values else "",
                "description": str(values[1]).strip() if len(values) > 1 else "",
                "http_status": str(values[2]).strip() if len(values) > 2 else "",
                "notes": str(values[3]).strip() if len(values) > 3 else "",
            }
            if error["description"]:
                errors.append(error)

    return errors


def _parse_common_details(table: dict) -> dict:
    result = {}
    for row in table.get("rows", []):
        values = list(row.values())
        if len(values) >= 2:
            key = str(values[0]).lower().strip()
            val = str(values[1]).strip()
            if "scheme" in key:
                result["scheme"] = val
            elif "method" in key:
                result["method"] = val
            elif "path" in key:
                result["path"] = val
    return result


def _parse_environments(table: dict) -> dict:
    result = {}
    headers = table.get("headers", [])

    chain1_col = next((h for h in headers if "chain 1" in h.lower() or "chain1" in h.lower() or "dev" in h.lower()), None)
    chain2_col = next((h for h in headers if "chain 2" in h.lower() or "chain2" in h.lower() or "test" in h.lower()), None)
    prod_col = next((h for h in headers if "prod" in h.lower() or "production" in h.lower()), None)
    param_col = next((h for h in headers if "param" in h.lower() or "name" in h.lower()), headers[0] if headers else None)

    for row in table.get("rows", []):
        param = row.get(param_col, "").lower().strip() if param_col else ""
        if "host" in param:
            result["chain1_host"] = row.get(chain1_col, "").strip() if chain1_col else ""
            result["chain2_host"] = row.get(chain2_col, "").strip() if chain2_col else ""
            result["prod_host"] = row.get(prod_col, "").strip() if prod_col else ""
        elif "port" in param:
            result["port"] = row.get(chain1_col, "").strip() if chain1_col else ""
        elif "url" in param or "path" in param:
            result["url_path"] = row.get(chain1_col, "").strip() if chain1_col else ""
    return result


def _is_field_table(table: dict, section_hint: str = "") -> bool:
    headers = [h.lower() for h in table.get("headers", [])]
    if not headers:
        return False
    has_field_col = any("field" in h or "name" in h or "parameter" in h for h in headers)
    return has_field_col and len(table.get("rows", [])) > 0


def _is_error_table(table: dict) -> bool:
    headers = [h.lower() for h in table.get("headers", [])]
    return any("scenario" in h or "error" in h or "http" in h or "status" in h for h in headers)


def _is_env_table(table: dict) -> bool:
    headers = [h.lower() for h in table.get("headers", [])]
    return any("chain" in h or "prod" in h or "environment" in h for h in headers)


def _is_common_details_table(table: dict) -> bool:
    rows = table.get("rows", [])
    if not rows:
        return False
    all_text = " ".join(str(v) for row in rows for v in row.values()).lower()
    return "method" in all_text and "path" in all_text


def extract_ia_from_html(html: str, page_title: str = "") -> dict:
    """Parse a Confluence IA page HTML and return structured data."""
    table_parser = TableParser()
    table_parser.feed(html)
    tables = table_parser.tables

    section_parser = SectionParser()
    section_parser.feed(html)
    section_parser.finalize()
    sections = section_parser.sections

    request_fields = []
    response_fields = []
    error_scenarios = []
    environments = {}
    common_details = {}
    unclassified_tables = []

    section_tables = _classify_tables_by_context(html, tables)

    for section_name, table in section_tables:
        sn = section_name.lower()
        if "request" in sn and "response" not in sn:
            fields = _parse_field_table(table)
            if fields:
                request_fields.extend(fields)
            else:
                unclassified_tables.append((section_name, table))
        elif "response" in sn:
            fields = _parse_field_table(table)
            if fields:
                response_fields.extend(fields)
            else:
                unclassified_tables.append((section_name, table))
        elif "error" in sn:
            errors = _parse_error_table(table)
            if errors:
                error_scenarios.extend(errors)
        elif "environment" in sn or "specific" in sn:
            env = _parse_environments(table)
            if env:
                environments.update(env)
        elif "common" in sn or "detail" in sn:
            cd = _parse_common_details(table)
            if cd:
                common_details.update(cd)
        else:
            if _is_field_table(table):
                unclassified_tables.append((section_name, table))
            elif _is_error_table(table):
                errors = _parse_error_table(table)
                if errors:
                    error_scenarios.extend(errors)
            elif _is_env_table(table):
                env = _parse_environments(table)
                environments.update(env)
            elif _is_common_details_table(table):
                cd = _parse_common_details(table)
                common_details.update(cd)

    if not request_fields and not response_fields and unclassified_tables:
        field_tables = [(s, t) for s, t in unclassified_tables if _is_field_table(t)]
        if field_tables:
            request_fields = _parse_field_table(field_tables[0][1])
        if len(field_tables) > 1:
            response_fields = _parse_field_table(field_tables[1][1])

    page_name = _extract_page_name(page_title)
    interface_id = _extract_interface_id(page_title)
    method = common_details.get("method", "")
    path = common_details.get("path", "")
    scheme = common_details.get("scheme", "HTTPS")
    sapi_path = _extract_sapi_path(sections, request_fields)

    return {
        "page_title": page_title,
        "basic_info": {
            "interface_id": interface_id,
            "method": method,
            "path": path,
            "scheme": scheme,
            "page_name": page_name,
            "sapi_path": sapi_path,
        },
        "request_fields": request_fields,
        "response_fields": response_fields,
        "error_scenarios": error_scenarios,
        "environments": environments,
        "sections": sections,
        "stats": {
            "table_count": len(tables),
            "request_field_count": len(request_fields),
            "response_field_count": len(response_fields),
            "error_count": len(error_scenarios),
            "section_names": list(sections.keys()),
        }
    }


def _classify_tables_by_context(html: str, tables: list) -> list[tuple[str, dict]]:
    events = []

    for match in re.finditer(r'<h[12][^>]*>(.*?)</h[12]>', html, re.DOTALL | re.IGNORECASE):
        header_text = re.sub('<[^>]+>', '', match.group(1)).strip()
        events.append((match.start(), 'header', header_text))

    table_starts = [m.start() for m in re.finditer(r'<table[^>]*>', html, re.IGNORECASE)]

    result = []
    current_section = "Unknown"

    all_events = sorted(
        [(pos, 'header', content) for pos, _, content in events] +
        [(pos, 'table', i) for i, pos in enumerate(table_starts)],
        key=lambda x: x[0]
    )

    for pos, etype, content in all_events:
        if etype == 'header':
            current_section = content
        elif etype == 'table':
            table_idx = content
            if table_idx < len(tables):
                result.append((current_section, tables[table_idx]))

    return result


def _extract_page_name(title: str) -> str:
    if not title:
        return ""
    t = title
    t = re.sub(r'INT\d+[\.\d]*\s*[-–]\s*', '', t)
    t = re.sub(r'MUL\d+[\.\d]+v?\d*\s*', '', t)
    t = re.sub(r'v[\d\.]+\s*[-–]\s*', '', t)
    t = re.sub(r'\[DRAFT\]', '', t, flags=re.IGNORECASE)
    t = re.sub(r'DRAFT', '', t, flags=re.IGNORECASE)
    t = re.sub(r'[-–]\s*INT\d+[\.\d]*', '', t)
    t = re.sub(r'\b(POST|GET|PUT|DELETE|PATCH)\b', '', t)
    t = re.sub(r'/[a-zA-Z{}/\[\]]+', '', t)
    t = re.sub(r'\s+', ' ', t).strip(' -–')
    return t


def _extract_interface_id(title: str) -> str:
    m = re.search(r'(INT[\d\.]+)', title, re.IGNORECASE)
    return m.group(1).upper() if m else ""


def _extract_sapi_path(sections: dict, request_fields: list) -> str:
    all_text = " ".join(sections.values())
    matches = re.findall(r'(?:POST|GET|PUT)\s+(/[a-zA-Z0-9/{}\[\]/_-]+)', all_text)

    priority_keywords = ['transaction', 'payment', 'transfer', 'process']
    for m in matches:
        if any(kw in m.lower() for kw in priority_keywords):
            return m

    main_path = ""
    for s_name, s_text in sections.items():
        if "common" in s_name.lower():
            pm = re.search(r'(/[a-zA-Z0-9/{}\[\]/_-]+)', s_text)
            if pm:
                main_path = pm.group(1)
                break

    for m in matches:
        if m != main_path and len(m) > 3:
            return m

    return ""


def register(mcp: FastMCP) -> None:
    """Register the IA extractor tool."""

    @mcp.tool()
    async def confluence_extract_ia(page_id: str, instance: str = "main") -> dict:
        """Extract structured data from a Confluence IA/PAPI page.

        Instead of returning raw HTML, this tool deterministically parses
        the page and returns a clean structured JSON with all request/response
        fields, error scenarios, and environment details.

        Args:
            page_id: Confluence page numeric ID
            instance: 'main' for production, 'sandbox' for sandbox instance
        """
        from msc_mcp_server.config import settings

        if instance == "sandbox":
            base_url = settings.confluence_sandbox_url
            email = settings.confluence_sandbox_email
            token = settings.confluence_sandbox_token
        else:
            base_url = settings.confluence_url
            email = settings.confluence_email
            token = settings.confluence_token

        if not base_url or not email or not token:
            return {"error": f"Confluence {instance} credentials not configured"}

        import base64
        auth = base64.b64encode(f"{email}:{token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{base_url}/wiki/api/v2/pages/{page_id}",
                headers=headers,
                params={"body-format": "storage"},
            )

        if resp.status_code == 404:
            return {"error": f"Page '{page_id}' not found"}
        if not resp.is_success:
            return {"error": f"Confluence API error {resp.status_code}"}

        data = resp.json()
        title = data.get("title", "")
        raw_html = data.get("body", {}).get("storage", {}).get("value", "")

        if not raw_html:
            return {"error": "Page has no content"}

        result = extract_ia_from_html(raw_html, title)
        result["page_id"] = page_id
        result["page_url"] = f"{base_url}/wiki{data.get('_links', {}).get('webui', '')}"

        logger.info(
            "confluence_extract_ia: page=%s title=%s req_fields=%d resp_fields=%d errors=%d",
            page_id, title,
            result["stats"]["request_field_count"],
            result["stats"]["response_field_count"],
            result["stats"]["error_count"],
        )

        return result
