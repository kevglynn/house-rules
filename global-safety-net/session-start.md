## house-rules — project bootstrap check

At session start, if the workspace root is a git repository AND **neither**
`.cursor/rules/` **nor** `.claude/rules/` is present AND the absolute
workspace path is not listed in `~/.house-rules-ignore` (if that file exists):
ask the user **once per session**:

> This project isn't bootstrapped with house-rules. Options:
>
> 1. Run `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" init --tool cursor|claude|both` to bootstrap
> 2. Skip for this session
> 3. Add this repo to `~/.house-rules-ignore` to silence this prompt permanently
>
> Which?

Act on the user's answer. If either rules directory is present, this block
is satisfied by the project's own rules — do not prompt.

If the user picks (1), confirm the tool choice before invoking, then pass
the chosen tool explicitly as `--tool cursor`, `--tool claude`, or
`--tool both`. Do not invoke `house-rules init` without a `--tool` flag or
an interactive terminal — the init refuses non-TTY invocation when the
tool isn't specified.

If `"${PROCESS_KIT:-$HOME/process-kit}"` does not exist, tell the
user to clone the kit first:

> house-rules is not installed at `~/process-kit`. Clone it
> with: `git clone https://github.com/kevglynn/house-rules ~/process-kit`

Do not re-ask in the same session after the user answers.
