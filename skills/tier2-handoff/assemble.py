#!/usr/bin/env python3
"""Deterministic Tier 2 review-prompt assembler.

Reads a JSON spec describing the prose sections and a list of source files,
embeds those files verbatim, and emits a ready-to-paste cross-model review
prompt. The output is byte-identical across runs given identical inputs:
nothing is read from the wall clock, environment, or network, and files are
embedded in the order the spec lists them.

The judgment (focus paragraph, context, already-addressed list) belongs to
the calling skill/agent and arrives via the spec. This script owns only the
mechanical, error-prone part: verbatim embedding and section scaffolding.

Usage:
    assemble.py --spec spec.json --root . [--out prompt.md]
    assemble.py --spec - < spec.json          # spec on stdin, prompt on stdout

Spec schema (JSON object):
    subject            (str, required)  short subject, e.g. "rate limiter"
    bead_id            (str, required)  e.g. "abc-123"
    language           (str, required)  e.g. "Rust", "TypeScript"
    artifact_noun      (str, required)  e.g. "token-bucket module"
    focus              (str, required)  the review-focus paragraph (agent-drafted)
    context            (str, required)  what the component is + spec references
    files              (list[str], required)  paths relative to --root, in embed order
    models             (list[str], optional)  default ["Grok", "Gemini", "GPT"]
    trusted_layers     (str, optional)  "do not re-review" boundary description
    rules              (list[str], optional)  domain rules the code must uphold
    already_addressed  (list[str], optional)  Tier 1 outcomes; "don't re-report"
    report_format      (str, optional)  override the default response-format ask
    out_of_scope       (str, optional)  default "Style and performance polish"

Exit codes: 0 ok; 2 bad spec / missing file; 1 unexpected error.
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_MODELS = ["Grok", "Gemini", "GPT"]
DEFAULT_OUT_OF_SCOPE = "Style and performance polish"
DEFAULT_REPORT_FORMAT = (
    "For each finding: severity (Critical / Important / Minor), file + location, "
    "what, why it matters, suggested fix. List rejected candidate findings with "
    "the reason for rejection. End with an overall verdict."
)

REQUIRED = ["subject", "bead_id", "language", "artifact_noun", "focus", "context", "files"]

# Extension → markdown code-fence language hint. Absent extensions get no hint.
LANG_HINT = {
    ".rs": "rust", ".py": "python", ".ts": "typescript", ".tsx": "tsx",
    ".js": "javascript", ".jsx": "jsx", ".go": "go", ".java": "java",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp", ".hpp": "cpp",
    ".rb": "ruby", ".sh": "bash", ".bash": "bash", ".sql": "sql",
    ".toml": "toml", ".yaml": "yaml", ".yml": "yaml", ".json": "json",
    ".md": "markdown", ".html": "html", ".css": "css", ".proto": "proto",
    ".kt": "kotlin", ".swift": "swift", ".rs.in": "rust",
}


def die(msg: str, code: int = 2) -> "None":
    sys.stderr.write(f"assemble.py: {msg}\n")
    raise SystemExit(code)


def fence_for(body: str) -> str:
    """Pick a backtick fence longer than any backtick run inside `body`, so
    files that themselves contain ``` embed without breaking the block."""
    longest = 0
    run = 0
    for ch in body:
        if ch == "`":
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return "`" * max(3, longest + 1)


def embed_file(path: Path, display: str) -> str:
    if not path.is_file():
        die(f"file not found: {display} (resolved to {path})")
    body = path.read_text(encoding="utf-8")
    fence = fence_for(body)
    hint = LANG_HINT.get(path.suffix, "")
    # Verbatim body; ensure the closing fence sits on its own line without
    # adding or dropping content from the source.
    sep = "" if body.endswith("\n") else "\n"
    return f"### {display}\n\n{fence}{hint}\n{body}{sep}{fence}\n"


def bullets(items) -> str:
    return "\n".join(f"- {line}" for line in items)


def build(spec: dict, root: Path) -> str:
    missing = [k for k in REQUIRED if k not in spec or spec[k] in (None, "", [])]
    if missing:
        die(f"spec missing required field(s): {', '.join(missing)}")

    models = spec.get("models") or DEFAULT_MODELS
    model_list = ", ".join(models)
    out_of_scope = spec.get("out_of_scope") or DEFAULT_OUT_OF_SCOPE
    report_format = spec.get("report_format") or DEFAULT_REPORT_FORMAT

    parts = []
    parts.append(f"# Tier 2 cross-model review — {spec['subject']} (`{spec['bead_id']}`)")
    parts.append(
        f"Paste everything below this line into each external model "
        f"({model_list}). Collect the responses and hand them back for triage."
    )
    parts.append("---")
    parts.append(
        f"Review this {spec['language']} {spec['artifact_noun']} with a critical "
        f"eye. Accept or reject each finding with a reason — don't rubber-stamp. "
        f"Focus on: {spec['focus']} {out_of_scope} is out of scope."
    )

    parts.append(f"## Context\n\n{spec['context']}")
    if spec.get("trusted_layers"):
        parts.append(
            f"The layers below are trusted, do not re-review: {spec['trusted_layers']}"
        )

    if spec.get("rules"):
        parts.append("## Rules this layer must uphold\n\n" + bullets(spec["rules"]))

    if spec.get("already_addressed"):
        parts.append(
            "## Already addressed (from prior review — don't re-report)\n\n"
            + bullets(spec["already_addressed"])
        )

    file_blocks = [embed_file((root / f), f) for f in spec["files"]]
    parts.append("## Files\n\n" + "\n".join(file_blocks).rstrip("\n"))

    parts.append(f"## Report format\n\n{report_format}")

    return "\n\n".join(parts) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic Tier 2 review-prompt assembler.")
    ap.add_argument("--spec", required=True, help="path to spec JSON, or - for stdin")
    ap.add_argument("--root", default=".", help="root for resolving file paths (default: cwd)")
    ap.add_argument("--out", default="-", help="output path, or - for stdout (default)")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.spec == "-" else Path(args.spec).read_text(encoding="utf-8")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"spec is not valid JSON: {e}")

    doc = build(spec, Path(args.root))

    if args.out == "-":
        sys.stdout.write(doc)
    else:
        Path(args.out).write_text(doc, encoding="utf-8")
        sys.stderr.write(f"assemble.py: wrote {len(doc)} bytes to {args.out}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
