from src.engine import sanitize_dom_snapshot

def test_sanitize_strips_scripts():
    raw_html = "<html><body><script>console.log('strip me');</script><p>Hello</p></body></html>"
    sanitized = sanitize_dom_snapshot(raw_html)
    assert "console.log" not in sanitized
    assert "<script>" not in sanitized
    assert "Hello" in sanitized

def test_sanitize_strips_styles():
    raw_html = "<html><head><style>body { color: red; }</style></head><body><p>Hello</p></body></html>"
    sanitized = sanitize_dom_snapshot(raw_html)
    assert "color: red" not in sanitized
    assert "<style>" not in sanitized
    assert "Hello" in sanitized

def test_sanitize_strips_links():
    raw_html = "<html><head><link rel='stylesheet' href='theme.css'></head><body><p>Hello</p></body></html>"
    sanitized = sanitize_dom_snapshot(raw_html)
    assert "theme.css" not in sanitized
    assert "Hello" in sanitized

def test_sanitize_strips_base64_data_uris():
    raw_html = '<div><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIA..." /><p>Text</p></div>'
    sanitized = sanitize_dom_snapshot(raw_html)
    assert "iVBORw0KGgoAAAANSUhEUgAAADIA" not in sanitized
    assert "[STRIPPED]" in sanitized
    assert "Text" in sanitized

def test_sanitize_strips_svg_paths():
    raw_html = '<button><svg viewBox="0 0 100 100"><path d="M 10,10 L 90,90 M 90,10 L 10,90" stroke="black" /></svg>Submit</button>'
    sanitized = sanitize_dom_snapshot(raw_html)
    assert "path" not in sanitized
    assert "M 10,10 L 90,90" not in sanitized
    assert "<svg" in sanitized
    assert "</svg>" in sanitized
    assert "Submit" in sanitized

def test_sanitize_strips_inline_styles():
    raw_html = '<div style="display: flex; justify-content: center;"><p>Content</p></div>'
    sanitized = sanitize_dom_snapshot(raw_html)
    assert "style=" not in sanitized
    assert "display: flex" not in sanitized
    assert "Content" in sanitized
