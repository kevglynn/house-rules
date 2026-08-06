#!/usr/bin/env python3
"""Render a gate/sprint packet markdown file to a self-contained HTML share.

Reads one packet markdown file, converts it to HTML, inlines a dark-theme CSS
and a heading-derived sidebar, and writes a single offline `<subject>-packet.html`.
Optionally verifies the packet against the blueprint constraints and checks
intra-page anchor integrity — all without a browser, so it runs in CI.

Usage:
    render.py --in docs/g2/packet.md --out docs/g2/g2-packet.html --title "Gate 2"
    render.py --in docs/g2/packet.md --verify           # checks only, no write
    render.py --in docs/g2/packet.md --out g2.html --verify   # write + check

Verification (headless — no browser needed):
    Blueprint constraints (from the gate-packet-blueprint):
      ERROR  no "Status at a glance" grid (markdown table)
      ERROR  FAQ has more than 5 entries (hard cap)
      ERROR  Receipts section does not have exactly 3 proofs
      WARN   no divergence strip (blockquote in the grid's eye-span)
      WARN   prose exceeds the 700-word target
    HTML integrity:
      ERROR  output is not well-formed HTML
      ERROR  an intra-page link (#anchor) resolves to no element id

Exit: 0 all checks pass (or render-only); 2 verification failed; 1 error.
"""

import argparse
import html.parser
import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.stderr.write("render.py: needs the 'markdown' package (pip install markdown)\n")
    raise SystemExit(1)

MD_EXT = ["tables", "fenced_code", "toc"]
PROSE_TARGET = 700

CSS = """
:root{--bg:#0e1116;--bg2:#151a22;--bg3:#1c2330;--ink:#e8e6e1;--ink-dim:#9aa3b2;
--accent:#f0b429;--accent2:#63b3ed;--good:#68d391;--warn:#fc8181;--border:#2a3242;
--maxw:860px;--sidebar:240px}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent2);text-decoration:none}a:hover{text-decoration:underline}
code{background:var(--bg3);padding:.12em .35em;border-radius:4px;font-size:.9em}
pre{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:14px;
overflow-x:auto;font-size:.82em;line-height:1.5}
pre code{background:none;padding:0}
h1,h2,h3,h4{font-family:Georgia,"Times New Roman",serif;font-weight:600;line-height:1.25}
del{color:var(--ink-dim)}
blockquote{border-left:3px solid var(--accent);margin:1em 0;padding:.3em 1em;
background:var(--bg2);border-radius:0 8px 8px 0}
table{border-collapse:collapse;width:100%;font-size:.9em;margin:1em 0;display:block;overflow-x:auto}
th,td{border:1px solid var(--border);padding:7px 10px;text-align:left;vertical-align:top;min-width:90px}
th{background:var(--bg3)}tr:nth-child(even){background:rgba(255,255,255,.02)}
details{background:var(--bg2);border:1px solid var(--border);border-radius:8px;margin:1em 0;padding:.4em 1em}
summary{cursor:pointer;font-weight:600}
#sidebar{position:fixed;inset:0 auto 0 0;width:var(--sidebar);background:var(--bg2);
border-right:1px solid var(--border);padding:22px 0;overflow-y:auto;z-index:10}
#sidebar .logo{font-family:Georgia,serif;font-size:1.2em;padding:0 20px 14px;color:var(--accent)}
#sidebar .logo small{display:block;color:var(--ink-dim);font-size:.6em;font-family:sans-serif;
letter-spacing:.1em;text-transform:uppercase;margin-top:4px}
#sidebar a{display:block;padding:7px 20px;color:var(--ink-dim);border-left:3px solid transparent;font-size:.9em}
#sidebar a:hover{color:var(--ink);text-decoration:none;background:var(--bg3)}
#sidebar a.active{color:var(--accent);border-left-color:var(--accent);background:var(--bg3)}
main{margin-left:var(--sidebar);padding:0 40px 120px;max-width:calc(var(--maxw) + var(--sidebar));}
article{max-width:var(--maxw);margin:0 auto;padding-top:30px}
article>h1{font-size:2.1em;color:var(--ink);margin-top:.6em}
article>h2{font-size:1.5em;color:var(--accent);border-bottom:1px solid var(--border);
padding-bottom:.3em;margin:1.6em 0 .7em}
article>h3{font-size:1.15em;color:var(--accent2)}
strong{color:var(--ink)}p,li{color:#c9cfd9}
#progress{height:4px;background:var(--accent);position:fixed;top:0;left:0;z-index:20;width:0}
@media(max-width:900px){#sidebar{display:none}main{margin-left:0;padding:0 18px 80px}}
@media print{#sidebar,#progress{display:none}main{margin:0;padding:0}
body{background:#fff;color:#111}table th,table td,blockquote,pre,details{background:#fff;border-color:#bbb}
p,li{color:#222}article>h2{color:#111}a{color:#0645ad}details{border:none}}
"""

JS = """
(function(){
  var links=[].slice.call(document.querySelectorAll('#sidebar a'));
  var secs=links.map(function(a){return document.querySelector(a.getAttribute('href'));});
  function spy(){var y=window.scrollY+120,act=0;
    secs.forEach(function(s,i){if(s&&s.offsetTop<=y)act=i;});
    links.forEach(function(a,i){a.classList.toggle('active',i===act);});
    var h=document.documentElement;
    document.getElementById('progress').style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';}
  window.addEventListener('scroll',spy);spy();
  window.addEventListener('beforeprint',function(){document.querySelectorAll('details').forEach(function(d){d.open=true;});});
})();
"""


def slugify(text: str) -> str:
    """Match python-markdown's toc slugifier closely enough for anchor checks."""
    s = re.sub(r"<[^>]+>", "", text)
    s = re.sub(r"[^\w\s-]", "", s.strip().lower())
    return re.sub(r"[\s]+", "-", s)


def to_html(md_text: str) -> str:
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", md_text)  # GFM strikethrough
    return markdown.markdown(text, extensions=MD_EXT)


def sidebar(md_text: str, title: str) -> str:
    heads = re.findall(r"^##\s+(.+?)\s*$", md_text, flags=re.M)
    items = "".join(
        f"<a href='#{slugify(h)}'>{re.sub(r'`', '', h)}</a>" for h in heads
    )
    return (
        f"<nav id='sidebar'><div class='logo'>{title}<small>packet</small></div>{items}</nav>"
    )


def build_page(md_text: str, title: str) -> str:
    body = to_html(md_text)
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{title} — packet</title><style>{CSS}</style></head><body>"
        "<div id='progress'></div>" + sidebar(md_text, title) +
        f"<main><article>{body}</article></main><script>{JS}</script></body></html>"
    )


# ------------------------------------------------------------- verification

def section(md_text: str, heading_re: str) -> str:
    """Return the body of the first section whose heading matches, up to the
    next same-or-higher-level heading."""
    m = re.search(rf"^(#{{1,6}})\s+{heading_re}\s*$", md_text, flags=re.M | re.I)
    if not m:
        return ""
    level = len(m.group(1))
    start = m.end()
    nxt = re.search(rf"^#{{1,{level}}}\s+\S", md_text[start:], flags=re.M)
    return md_text[start: start + nxt.start()] if nxt else md_text[start:]


def strip_code(md_text: str) -> str:
    return re.sub(r"```.*?```", "", md_text, flags=re.S)


def prose_word_count(md_text: str) -> int:
    body = strip_code(md_text)
    words = 0
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "|", "<", ">")) or set(s) <= {"-", "|", ":", " "}:
            continue
        words += len(re.findall(r"\S+", s))
    return words


class _Wellformed(html.parser.HTMLParser):
    """Minimal well-formedness + id/href collector."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.ids = set()
        self.anchors = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.add(d["id"])
        if tag == "a" and d.get("href", "").startswith("#"):
            self.anchors.append(d["href"][1:])
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass


def verify(md_text: str, page_html: str) -> int:
    errors, warns = [], []

    grid = section(md_text, r"Status at a glance")
    if "|" not in grid:
        errors.append("no 'Status at a glance' grid (markdown table) found")

    faq = section(md_text, r"FAQ")
    faq_entries = len(re.findall(r"^\*\*.+\*\*\s*$", faq, flags=re.M))
    faq_entries += len(re.findall(r"^#{3,6}\s+\S", faq, flags=re.M))
    if faq_entries > 5:
        errors.append(f"FAQ has {faq_entries} entries; the hard cap is 5")

    receipts = section(md_text, r"Receipts")
    receipt_proofs = len(re.findall(r"^\*\*.+\*\*", receipts, flags=re.M))
    if receipts and receipt_proofs != 3:
        errors.append(f"Receipts has {receipt_proofs} proofs; the blueprint is exactly 3")
    elif not receipts:
        errors.append("no Receipts section found")

    # divergence strip: a blockquote in the grid's eye-span. The window is
    # structural — the "Status at a glance" section from its heading through
    # the END of the grid table plus a short margin — never a fixed character
    # offset: grid rows carry linked evidence of arbitrary width, and a fixed
    # 1800-char window false-WARNed template-conformant packets, which trains
    # authors to ignore the verifier (found live on a consuming project's
    # gate packet). A strip placed above the grid (equally in the eye-span;
    # the order that live packet used) sits inside the same window.
    grid_lines = [m.end() for m in re.finditer(r"^\|.*$", grid, flags=re.M)]
    strip_zone = grid[: (grid_lines[-1] + 600) if grid_lines else 0]
    if not re.search(r"^>\s+\S", strip_zone, flags=re.M):
        warns.append("no divergence strip (blockquote) in the grid's eye-span")

    words = prose_word_count(md_text)
    if words > PROSE_TARGET:
        warns.append(f"prose is ~{words} words; target is <= {PROSE_TARGET}")

    parser = _Wellformed()
    parser.feed(page_html)
    if parser.stack:
        errors.append(f"HTML not well-formed; unclosed tags: {parser.stack}")
    dangling = sorted(a for a in parser.anchors if a and a not in parser.ids)
    if dangling:
        errors.append(f"intra-page links resolve to no id: {', '.join('#' + a for a in dangling)}")

    for w in warns:
        sys.stderr.write(f"  WARN  {w}\n")
    for e in errors:
        sys.stderr.write(f"  ERROR {e}\n")
    if errors:
        sys.stderr.write(f"render.py: verification FAILED ({len(errors)} error(s), {len(warns)} warning(s))\n")
        return 2
    sys.stderr.write(f"render.py: verification passed ({len(warns)} warning(s); prose ~{words} words)\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Render a gate/sprint packet to a self-contained HTML share.")
    ap.add_argument("--in", dest="inp", required=True, help="packet markdown path")
    ap.add_argument("--out", help="output HTML path (omit for verify-only)")
    ap.add_argument("--title", default="", help="share title (default: first H1)")
    ap.add_argument("--verify", action="store_true", help="run blueprint + anchor checks")
    args = ap.parse_args()

    md_text = Path(args.inp).read_text(encoding="utf-8")
    title = args.title or (re.search(r"^#\s+(.+?)\s*$", md_text, flags=re.M) or [None, "Packet"])[1]
    title = re.sub(r"`|·.*$", "", title).strip() if title else "Packet"

    page = build_page(md_text, title)

    if args.out:
        Path(args.out).write_text(page, encoding="utf-8")
        sys.stderr.write(f"render.py: wrote {len(page)} bytes to {args.out}\n")

    if args.verify or not args.out:
        return verify(md_text, page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
