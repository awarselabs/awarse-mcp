import re

def sanitize_dom_snapshot(html_content: str) -> str:
    """
    Sanitizes the HTML/DOM snapshot to minimize token consumption:
    - Strips all <script>...</script> blocks.
    - Strips all <style>...</style> blocks.
    - Strips all <link ...> tags.
    - Strips or truncates base64 data URIs in src, href, or other attributes.
    - Strips all path/polygon/shape data inside <svg>...</svg> elements, leaving just the tags.
    - Strips inline styles (e.g. style="...").
    - Strips comments.
    - Collapses duplicate whitespaces.
    """
    if not html_content:
        return ""

    # 1. Strip <script> tags and their contents
    html_content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script\s*>', '', html_content, flags=re.IGNORECASE)

    # 2. Strip <style> tags and their contents
    html_content = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style\s*>', '', html_content, flags=re.IGNORECASE)

    # 3. Strip <link> tags
    html_content = re.sub(r'<link\b[^>]*>', '', html_content, flags=re.IGNORECASE)

    # 4. Truncate base64 data URIs in attributes
    html_content = re.sub(
        r'("data:[^";]+;base64,)([^"]{10,})"',
        r'\1[STRIPPED]"',
        html_content
    )
    html_content = re.sub(
        r"('data:[^';]+;base64,)([^']{10,})'",
        r"\1[STRIPPED]'",
        html_content
    )

    # 5. Strip SVG contents to retain only the opening/closing tags
    def clean_svg(match):
        opening_tag = match.group(1)
        return f"{opening_tag}</svg>"

    html_content = re.sub(r'(<svg\b[^>]*>)(.*?)(<\/svg\s*>)', clean_svg, html_content, flags=re.IGNORECASE | re.DOTALL)

    # 6. Strip comments
    html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)

    # 7. Strip inline styles (e.g. style="...")
    html_content = re.sub(r'\sstyle="[^"]*"', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r"\sstyle='[^']*'", '', html_content, flags=re.IGNORECASE)

    # 8. Clean up extra whitespace and empty lines
    lines = [line.strip() for line in html_content.splitlines()]
    lines = [line for line in lines if line]
    html_content = "\n".join(lines)

    # Normalize multiple consecutive spaces
    html_content = re.sub(r'[ \t]+', ' ', html_content)

    return html_content
