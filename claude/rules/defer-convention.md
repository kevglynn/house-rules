# Defer Convention

Mark deliberate simplifications with a `defer:` comment:

```
// defer: <what was simplified>. ceiling: <known limitation>. upgrade when: <trigger condition>.
```

Language-appropriate comment prefix (`//`, `#`, `/* */`, `--`); the ceiling and trigger may continue on the following comment line(s).

**The no-trigger law:** every `defer:` comment MUST include an "upgrade when:" condition. A deferral without a trigger is just a TODO with a fancier name. If you can't name when to revisit, either the simplification is permanent (no comment needed) or you don't understand the ceiling yet (investigate before deferring).

Marker choice: `defer:` = deliberate simplification with known limits (structured — ceiling + trigger required); `TODO` = unstructured reminder; `FIXME` = actually broken.

**Checker:** `scripts/defer-lint` (kit-distributed) verifies the law — exit 1 on any defer lacking its upgrade-when clause; `--json` for agents; worked good/bad examples in `defer-lint --help`. Harvesting deferrals into a debt ledger: the `graybeard-debt` skill.
