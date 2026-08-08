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
    assemble.py --spec spec.json --root . [--out prompt.md] [--exploit-out exploit.md]
    assemble.py --spec - < spec.json          # spec on stdin, prompt on stdout

Spec schema (JSON object):
    subject            (str, required)  short subject, e.g. "rate limiter"
    bead_id            (str, required)  e.g. "abc-123"
    language           (str, required)  e.g. "Rust", "TypeScript"
    artifact_noun      (str, required)  e.g. "token-bucket module"
    focus              (str, required)  the review-focus paragraph (agent-drafted)
    context            (str, required)  what the component is + what was done and why + spec references
    files              (list[str], required)  paths relative to --root, in embed order
    models             (list[str], optional)  concrete reviewer lanes; when
                                              absent the prompt describes
                                              archetypes and names no vendor
    trusted_layers     (str, optional)  "do not re-review" boundary description
    rules              (list[str], optional)  domain rules the code must uphold
    already_addressed  (list[str], optional)  Tier 1 outcomes; "don't re-report"
    report_format      (str, optional)  override the default response-format ask
    out_of_scope       (str, optional)  default "Style and performance polish"
    discipline         (list[str], optional)  override the default review-discipline rules
    exploit_focus      (str, optional)  charter for --exploit-out; defaults to `focus`

--exploit-out emits a companion prompt with the same embeds but an
adversarial-verification mandate instead of a review mandate: the deliverable
is a demonstrated invariant violation (concrete input + line-level code path)
or a per-property proof that none exists. Intended for a separate instance of
a model — a second window, not a lane that already reviewed this change — so
its output stays independent of the review framing. (The flag name is
historical; the emitted prompt is phrased in counterexample terms, not attack
terms.)

Exit codes: 0 ok; 2 bad spec / missing file; 1 unexpected error.
"""

import argparse
import json
import sys
from pathlib import Path

# No default lineup. A named set of vendors is project-specific
# configuration, and this skill ships to third-party repos where those names
# are wrong, unavailable, or simply stale — model names age faster than
# anything else in the kit. With no lineup supplied, the prompt describes
# reviewer archetypes and leaves resolution to whoever runs it, matching how
# skills/council resolves its voices.
DEFAULT_LANE_ARCHETYPES = (
    "the strongest reasoning model available to you, a capable model from a "
    "different family, and a third family where one is available"
)
DEFAULT_OUT_OF_SCOPE = "Style and performance polish"
DEFAULT_REPORT_FORMAT = (
    "For each finding: severity (Critical / Important / Minor), file + location, "
    "what, why it matters, suggested fix. List rejected candidate findings with "
    "the reason for rejection. End with an overall verdict."
)

# Review-discipline rules emitted into every prompt. Each targets a failure
# mode observed across real triage rounds: clean verdicts issued without
# verification, real findings self-rejected as "out of scope", and packet
# claims (context / already-addressed / trusted boundary) taken on faith.
DEFAULT_DISCIPLINE = [
    "Verdicts require evidence. For every focus area and every finding — "
    "including a clean pass — quote the exact code that decides your "
    "conclusion. A verdict without quoted code is invalid.",
    "Scope objections are not rejections. A real defect that falls outside "
    "this change's scope is still a finding — report it tagged out-of-scope. "
    "Triage owns scope decisions, not you; never self-reject a finding you "
    "believe is real.",
    "The packet's claims — the context, the already-addressed list, the "
    "trusted-layer boundary — are assertions, not facts. Verify the ones "
    "your verdict depends on; disproving one counts as a finding.",
]

# Report format for the companion adversarial-verification prompt. Kept in
# counterexample terms rather than attack/exploit terms: the analytical demand
# is identical (a concrete violating input + the code path, or a per-property
# proof of absence), but the wording avoids tripping provider safety filters
# tuned for offensive-security requests.
EXPLOIT_REPORT_FORMAT = (
    "Report demonstrated violations in order of severity. For each: the exact "
    "input, request sequence, or interleaving; the expected-per-contract vs "
    "actual behavior; the code path (file + location) that admits it; and a "
    "suggested fix. If you found none, list every property you probed with the "
    "quoted code that rules a violation out. End with a verdict: VIOLATION "
    "FOUND, or NO VIOLATION after N probed properties."
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

    models = spec.get("models")
    out_of_scope = spec.get("out_of_scope") or DEFAULT_OUT_OF_SCOPE
    report_format = spec.get("report_format") or DEFAULT_REPORT_FORMAT

    parts = []
    parts.append(f"# Tier 2 cross-model review — {spec['subject']} (`{spec['bead_id']}`)")
    if models:
        lanes = f"each external model ({', '.join(models)})"
    else:
        lanes = (
            f"each of three independent reviewer lanes — "
            f"{DEFAULT_LANE_ARCHETYPES}. Never invent a model name; pick from "
            f"what your environment actually offers"
        )
    parts.append(
        f"Paste everything below this line into {lanes}. Collect the "
        f"responses and hand them back for triage."
    )
    parts.append("---")
    parts.append(
        f"Review this {spec['language']} {spec['artifact_noun']} with a critical "
        f"eye. Accept or reject each finding with a reason — don't rubber-stamp. "
        f"Focus on: {spec['focus']} {out_of_scope} is out of scope."
    )

    parts.append(
        "## Review discipline\n\n" + bullets(spec.get("discipline") or DEFAULT_DISCIPLINE)
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


def build_exploit(spec: dict, root: Path) -> str:
    """Companion adversarial-verification prompt: same embeds, counterexample
    mandate.

    Deliberately omits the review framing so a separate model instance
    stress-tests the code instead of auditing it. Shares the spec's context,
    rules, and already-addressed list (so effort doesn't land on fixed
    ground). Phrased in counterexample terms rather than attack/exploit terms
    — same analytical demand, without the wording that trips offensive-
    security safety filters."""
    missing = [k for k in REQUIRED if k not in spec or spec[k] in (None, "", [])]
    if missing:
        die(f"spec missing required field(s): {', '.join(missing)}")

    focus = spec.get("exploit_focus") or spec["focus"]

    parts = []
    parts.append(
        f"# Tier 2 adversarial verification — {spec['subject']} (`{spec['bead_id']}`)"
    )
    parts.append(
        "Paste everything below this line into a separate model instance — "
        "not the one that produced a review of this change. Collect the "
        "response and hand it back for triage."
    )
    parts.append("---")
    parts.append(
        f"You are not writing a general review of this {spec['language']} "
        f"{spec['artifact_noun']} — you are stress-testing its invariants. "
        f"For each rule below and each property named in the charter, try to "
        f"construct a concrete counterexample: an input, request sequence, or "
        f"interleaving that makes the code violate it. Your deliverable is "
        f"either a demonstrated violation — the exact inputs and the "
        f"line-level code path that produces it — or, for each property you "
        f"probed, the quoted code that rules a violation out. \"Looks fine\" "
        f"is not a deliverable. Charter: {focus}"
    )

    parts.append(f"## Context\n\n{spec['context']}")
    if spec.get("trusted_layers"):
        parts.append(
            f"The layers below are trusted; probe the change, not its "
            f"substrate: {spec['trusted_layers']}"
        )

    if spec.get("rules"):
        parts.append(
            "## Invariants to test (a demonstrated violation of any is a finding)\n\n"
            + bullets(spec["rules"])
        )

    if spec.get("already_addressed"):
        parts.append(
            "## Already fixed (probing here is wasted effort — don't re-report)\n\n"
            + bullets(spec["already_addressed"])
        )

    file_blocks = [embed_file((root / f), f) for f in spec["files"]]
    parts.append("## Files\n\n" + "\n".join(file_blocks).rstrip("\n"))

    parts.append(f"## Report format\n\n{EXPLOIT_REPORT_FORMAT}")

    return "\n\n".join(parts) + "\n"


def _emit(doc: str, out: str, label: str) -> None:
    if out == "-":
        sys.stdout.write(doc)
    else:
        Path(out).write_text(doc, encoding="utf-8")
        sys.stderr.write(f"assemble.py: wrote {len(doc)} bytes to {out} ({label})\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic Tier 2 review-prompt assembler.")
    ap.add_argument("--spec", required=True, help="path to spec JSON, or - for stdin")
    ap.add_argument("--root", default=".", help="root for resolving file paths (default: cwd)")
    ap.add_argument("--out", default="-", help="review-prompt output path, or - for stdout (default)")
    ap.add_argument(
        "--exploit-out",
        default=None,
        help="also emit the companion exploit-construction prompt to this path (or - for stdout)",
    )
    args = ap.parse_args()

    raw = sys.stdin.read() if args.spec == "-" else Path(args.spec).read_text(encoding="utf-8")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"spec is not valid JSON: {e}")

    root = Path(args.root)

    if args.exploit_out == "-" and args.out == "-":
        die("--out and --exploit-out cannot both be stdout; give at least one a path")

    _emit(build(spec, root), args.out, "review")
    if args.exploit_out is not None:
        _emit(build_exploit(spec, root), args.exploit_out, "exploit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
