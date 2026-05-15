"""Confluence Markdown Converter — converts Confluence Storage Format to clean Markdown.

Transforms raw Confluence HTML (200K+ chars) into clean, LLM-friendly Markdown (~30-50K).
Works for ANY Confluence page structure — no hardcoded assumptions about sections or columns.

Key conversions:
- Tables → Markdown tables with | col | col | format
- H1/H2/H3 → # / ## / ### headers
- Bold/italic/code → **bold** / *italic* / `code`
- Lists → - items
- Strips all Confluence macros (TOC, PlantUML diagrams etc)
- Preserves all text content
"""

import logging
import re
from html.parser import HTMLParser

import httpx
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


class ConfluenceToMarkdown(HTMLParser):
    """Stateful HTML parser that converts Confluence storage format to Markdown."""

    def __init__(self):
        super().__init__()
        self.output: list[str] = []
        self._stack: list[str] = []
        self._table_headers: list[str] = []
        self._table_rows: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []
        self._in_table = False
        self._in_cell = False
        self._is_header_cell = False
        self._table_depth = 0
        self._skip_content = False
        self._skip_depth = 0
        self._list_depth = 0
        self._in_code = False
        self._current_section: list[str] = []
        self._in_pre = False
        self._in_code_macro = False
        self._code_macro_lang = ""
        self._code_macro_content = []
        self._in_cdata = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "ac:structured-macro":
            macro_name = attrs_dict.get("ac:name", "")
            if macro_name == "code":
                self._in_code_macro = True
                self._code_macro_lang = ""
                self._code_macro_content = []
                return
            elif macro_name in ("toc", "plantuml"):
                self._skip_content = True
                self._skip_depth = 1
                return

        if self._skip_content:
            self._skip_depth += 1
            return

        self._stack.append(tag)

        if tag == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._in_table = True
                self._table_headers = []
                self._table_rows = []

        elif tag == "tr":
            if self._table_depth == 1:
                self._current_row = []

        elif tag in ("th", "td"):
            if self._table_depth == 1:
                self._current_cell = []
                self._in_cell = True
                self._is_header_cell = (tag == "th")

        elif tag in ("h1", "h2", "h3", "h4"):
            self._flush_buffer()
            self._current_section = []

        elif tag == "pre":
            lang = attrs_dict.get("data-lang", "")
            self._flush_buffer()
            self._current_section = [f"\n```{lang}\n"]
            self._in_pre = True

        elif tag in ("ul", "ol"):
            self._list_depth += 1

        elif tag == "li":
            self._current_section.append("\n" + "  " * (self._list_depth - 1) + "- ")

        elif tag == "br":
            if self._in_cell:
                self._current_cell.append(" ")
            else:
                self._current_section.append("\n")

        elif tag == "strong" or tag == "b":
            if self._in_cell:
                self._current_cell.append("**")
            else:
                self._current_section.append("**")

        elif tag == "em" or tag == "i":
            if self._in_cell:
                self._current_cell.append("*")
            else:
                self._current_section.append("*")

        elif tag == "code":
            self._in_code = True
            if self._in_cell:
                self._current_cell.append("`")
            else:
                self._current_section.append("`")

        elif tag == "a":
            href = attrs_dict.get("href", "")
            if href and not href.startswith("#"):
                self._stack[-1] = f"a[{href}]"

    def handle_endtag(self, tag):
        if self._skip_content:
            self._skip_depth -= 1
            if self._skip_depth == 0:
                self._skip_content = False
            return

        if tag == "ac:structured-macro" and self._in_code_macro:
            content = "".join(self._code_macro_content).strip()
            if content:
                lang = self._code_macro_lang or ""
                self._flush_to_output(f"\n```{lang}\n{content}\n```\n")
            self._in_code_macro = False
            self._code_macro_content = []
            self._code_macro_lang = ""
            return

        if tag == "ac:parameter" and self._in_code_macro:
            return

        current = self._stack.pop() if self._stack else tag

        if tag == "table":
            self._table_depth -= 1
            if self._table_depth == 0:
                self._flush_table()
                self._in_table = False

        elif tag == "tr" and self._table_depth == 1:
            if self._is_header_row():
                self._table_headers = [c.strip() for c in self._current_row]
            else:
                if any(c.strip() for c in self._current_row):
                    self._table_rows.append([c.strip() for c in self._current_row])
            self._current_row = []

        elif tag in ("th", "td") and self._table_depth == 1:
            cell_content = " ".join(self._current_cell).strip()
            cell_content = re.sub(r'\s+', ' ', cell_content)
            self._current_row.append(cell_content)
            self._current_cell = []
            self._in_cell = False

        elif tag == "h1":
            text = "".join(self._current_section).strip()
            if text:
                self._flush_to_output(f"\n# {text}\n")
            self._current_section = []

        elif tag == "h2":
            text = "".join(self._current_section).strip()
            if text:
                self._flush_to_output(f"\n## {text}\n")
            self._current_section = []

        elif tag == "h3":
            text = "".join(self._current_section).strip()
            if text:
                self._flush_to_output(f"\n### {text}\n")
            self._current_section = []

        elif tag == "h4":
            text = "".join(self._current_section).strip()
            if text:
                self._flush_to_output(f"\n#### {text}\n")
            self._current_section = []

        elif tag == "pre":
            content = "".join(self._current_section)
            if content.startswith("\n```"):
                self._flush_to_output(content + "\n```\n")
            self._current_section = []
            self._in_pre = False

        elif tag in ("p",):
            if not self._in_table and not self._in_pre:
                text = "".join(self._current_section).strip()
                if text:
                    self._flush_to_output(text + "\n")
                self._current_section = []

        elif tag in ("ul", "ol"):
            self._list_depth -= 1
            if self._list_depth == 0:
                text = "".join(self._current_section)
                if text.strip():
                    self._flush_to_output(text + "\n")
                self._current_section = []

        elif tag in ("strong", "b"):
            if self._in_cell:
                self._current_cell.append("**")
            else:
                self._current_section.append("**")

        elif tag in ("em", "i"):
            if self._in_cell:
                self._current_cell.append("*")
            else:
                self._current_section.append("*")

        elif tag == "code":
            self._in_code = False
            if self._in_cell:
                self._current_cell.append("`")
            else:
                self._current_section.append("`")

    def handle_data(self, data):
        if self._skip_content:
            return

        if self._in_code_macro:
            self._code_macro_content.append(data)
            return

        text = data.replace("\xa0", " ")

        if self._in_cell and self._table_depth == 1:
            self._current_cell.append(text)
        elif not self._in_table:
            self._current_section.append(text)

    def _is_header_row(self) -> bool:
        return not self._table_headers and len(self._current_row) > 0

    def _flush_table(self):
        if not self._table_headers and not self._table_rows:
            return

        headers = self._table_headers or [f"Col{i+1}" for i in range(
            max(len(r) for r in self._table_rows) if self._table_rows else 1
        )]

        n_cols = len(headers)
        rows = []
        for row in self._table_rows:
            padded = row + [""] * (n_cols - len(row))
            rows.append(padded[:n_cols])

        lines = []
        header_line = "| " + " | ".join(h.replace("|", "\\|") for h in headers) + " |"
        sep_line = "| " + " | ".join("---" for _ in headers) + " |"
        lines.append(header_line)
        lines.append(sep_line)

        for row in rows:
            cells = [c.replace("|", "\\|").replace("\n", " ") for c in row]
            lines.append("| " + " | ".join(cells) + " |")

        self._flush_to_output("\n" + "\n".join(lines) + "\n")

    def _flush_buffer(self):
        text = "".join(self._current_section).strip()
        if text:
            self._flush_to_output(text + "\n")
        self._current_section = []

    def _flush_to_output(self, text: str):
        self.output.append(text)

    def get_markdown(self) -> str:
        self._flush_buffer()
        result = "".join(self.output)
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()


def html_to_markdown(html: str, base_url: str = "https://msccruises.atlassian.net") -> str:
    """Convert Confluence storage format HTML to clean Markdown."""

    def replace_code_macro(m):
        block = m.group(0)
        lang_match = re.search(r'<ac:parameter ac:name="language">(.*?)</ac:parameter>', block)
        lang = lang_match.group(1).strip() if lang_match else ""
        cdata_match = re.search(r'<!\[CDATA\[(.*?)\]\]>', block, re.DOTALL)
        content = cdata_match.group(1) if cdata_match else ""
        if content.strip():
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return f'<pre data-lang="{lang}">{content}</pre>'
        return ''

    html = re.sub(
        r'<ac:structured-macro ac:name="code".*?</ac:structured-macro>',
        replace_code_macro, html, flags=re.DOTALL
    )

    def unwrap_content_macros(html: str) -> str:
        OPEN = '<ac:structured-macro'
        CLOSE = '</ac:structured-macro>'
        CONTENT_MACROS = {"expand", "info", "warning", "note", "tip"}
        result = html
        max_passes = 30
        for _ in range(max_passes):
            start_match = re.search(
                r'<ac:structured-macro ac:name="(' + '|'.join(CONTENT_MACROS) + r')"',
                result
            )
            if not start_match:
                break
            start_pos = start_match.start()
            depth = 1
            pos = start_match.end()
            end_pos = None
            while pos < len(result) and depth > 0:
                next_open = result.find(OPEN, pos)
                next_close = result.find(CLOSE, pos)
                if next_close == -1:
                    break
                if next_open != -1 and next_open < next_close:
                    depth += 1
                    pos = next_open + len(OPEN)
                else:
                    depth -= 1
                    if depth == 0:
                        end_pos = next_close + len(CLOSE)
                    pos = next_close + len(CLOSE)
            if end_pos is None:
                break
            block = result[start_pos:end_pos]
            title_match = re.search(r'<ac:parameter ac:name="title">(.*?)</ac:parameter>', block)
            title = title_match.group(1).strip() if title_match else start_match.group(1).upper()
            body_match = re.search(r'<ac:rich-text-body>(.*?)</ac:rich-text-body>', block, re.DOTALL)
            body = body_match.group(1).strip() if body_match else ""
            replacement = f'<p><strong>[{title}]</strong></p>{body}' if body else f'<p><em>[{title}]</em></p>'
            result = result[:start_pos] + replacement + result[end_pos:]
        return result

    html = unwrap_content_macros(html)

    html = re.sub(
        r'<ac:structured-macro ac:name="plantuml".*?</ac:structured-macro>',
        '<p><em>[Sequence Diagram — omitted]</em></p>', html, flags=re.DOTALL
    )

    def replace_status(m):
        block = m.group(0)
        title_match = re.search(r'<ac:parameter ac:name="title">(.*?)</ac:parameter>', block)
        title = title_match.group(1).strip() if title_match else "STATUS"
        return f' **[{title}]**'

    html = re.sub(
        r'<ac:structured-macro ac:name="status".*?</ac:structured-macro>',
        replace_status, html, flags=re.DOTALL
    )

    html = re.sub(r'<ac:structured-macro.*?</ac:structured-macro>', '', html, flags=re.DOTALL)

    def replace_ac_link(m):
        block = m.group(0)
        page_title = ""
        title_match = re.search(r'ri:content-title="([^"]+)"', block)
        if title_match:
            page_title = title_match.group(1)
        body_match = re.search(r'<ac:link-body>(.*?)</ac:link-body>', block, re.DOTALL)
        link_text = re.sub('<[^>]+>', '', body_match.group(1)).strip() if body_match else page_title
        if not link_text:
            link_text = page_title or "link"
        if page_title:
            return f'[{link_text}]({base_url}/wiki/spaces/DTP/search?text={page_title.replace(" ", "+")})'
        return link_text

    html = re.sub(r'<ac:link>.*?</ac:link>', replace_ac_link, html, flags=re.DOTALL)
    html = re.sub(r'<ac:image.*?</ac:image>', '[Image]', html, flags=re.DOTALL)
    html = re.sub(r'<ac:inline-comment-marker[^>]*>', '', html)
    html = re.sub(r'</ac:inline-comment-marker>', '', html)
    html = re.sub(r'<ac:layout[^>]*>', '', html)
    html = re.sub(r'</ac:layout>', '', html)
    html = re.sub(r'<ac:layout-section[^>]*>', '', html)
    html = re.sub(r'</ac:layout-section>', '', html)
    html = re.sub(r'<ac:layout-cell[^>]*>', '', html)
    html = re.sub(r'</ac:layout-cell>', '', html)
    html = re.sub(r'<ac:[a-z-]+[^>]*/>', '', html)
    html = re.sub(r'<ac:[a-z-]+[^>]*>.*?</ac:[a-z-]+>', '', html, flags=re.DOTALL)

    parser = ConfluenceToMarkdown()
    parser.feed(html)
    return parser.get_markdown()


def register(mcp: FastMCP) -> None:
    """Register confluence_get_markdown tool."""

    @mcp.tool()
    async def confluence_get_markdown(page_id: str, instance: str = "main") -> dict:
        """Get a Confluence page as clean Markdown instead of raw HTML.

        Converts Confluence Storage Format HTML to clean, LLM-friendly Markdown.
        Use this for ANY Confluence page when you need to read/understand content.

        Args:
            page_id: Confluence page numeric ID (from URL)
            instance: 'main' for production, 'sandbox' for sandbox instance
        """
        from msc_mcp_server.config import settings
        import base64

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

        auth = base64.b64encode(f"{email}:{token}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

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

        markdown = html_to_markdown(raw_html)

        logger.info(
            "confluence_get_markdown: page=%s title=%s html=%d md=%d (%.0f%%)",
            page_id, title, len(raw_html), len(markdown),
            len(markdown) / len(raw_html) * 100
        )

        return {
            "page_id": page_id,
            "title": title,
            "url": f"{base_url}/wiki{data.get('_links', {}).get('webui', '')}",
            "markdown": markdown,
            "stats": {
                "html_size": len(raw_html),
                "markdown_size": len(markdown),
                "reduction_pct": round((1 - len(markdown) / len(raw_html)) * 100),
            }
        }
