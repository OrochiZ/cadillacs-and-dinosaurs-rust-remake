#!/usr/bin/env python3
"""Static doc/code consistency checks for the release checklist (M10-26).

The port's documents drift from the code and from the repo over time (a milestone
table left at "Pending", a known difference that was fixed, an asset dump that left
git). Those are cheap to catch mechanically but easy to miss by eye.

No ROM access, no game code changes, no third-party packages. Run from anywhere:

    python re/harness/check_docs.py

Exits 0 when every check passes, 1 with a list of problems. Each check is a pure
parse function plus a comparison, so a regression can be reproduced from any past
revision with `git show REV:path | ...`.

Checks:
  1. milestone status: plan/PLAN.md's short map vs STATUS.md (authoritative).
  2. jump names: the --jump table in run.md vs JUMPS in jumps.rs.
  3. config keys: README's Available Settings vs OPTIONS in config.rs.
  4. CLI flags: flags named in run.md / README exist as strings in the Rust crates.
  5. git leak: no ROM-derived data is tracked (M10-26 release checklist).
  6. known differences: README must not list a difference final.txt marks GONE.
     This one is a sentinel table, not a semantic parser: when a new cause is
     marked GONE in final.txt, add its marker below with the source. It is kept
     explicit on purpose rather than guessing at prose.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

# cargo / libtest own these, and one game flag lives in dino-extract (rom.rs).
CARGO_FLAGS = {"--release", "--nocapture", "--ignored"}
ROM_SUFFIXES = (".zip", ".bin", ".rom", ".npy", ".png", ".gif", ".jpg",
                ".elf", ".state", ".trc", ".wav", ".mp3")
ROM_PREFIXES = ("re/rom/", "re/out/", "re/ghidra/proj/", "re/ghidra/log")

# README's "Known Differences" is for a player. A difference whose cause is
# marked GONE in final.txt must not be advertised as current. (marker, source)
GONE_MARKERS = (
    ("Fessenden with three heroes", "final.txt N1 (GONE: M10-19 / M10-20 merge)"),
)


def read(root: pathlib.Path, rel: str) -> str:
    path = root / rel
    if not path.is_file():
        raise FileNotFoundError(f"missing required file: {rel}")
    return path.read_text(encoding="utf-8")


def parse_milestones(text: str) -> dict[str, str]:
    """`| M0 | ... | Done (...) |` -> {'M0': 'Done'}; the state is column index 4."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        if not re.match(r"^\|\s*M\d+\s*\|", line):
            continue
        cols = line.split("|")
        if len(cols) < 6:
            continue
        state = cols[4].strip()
        word = state.split()[0] if state else ""
        # "In progress" is two words; everything else of interest is one word.
        if state.lower().startswith("in progress"):
            word = "In progress"
        out[cols[1].strip()] = word
    return out


def parse_jump_table(text: str) -> set[str]:
    return set(re.findall(r"^\|\s*(ep[0-9][a-z0-9]*)\s*\|", text, re.M))


def parse_jump_source(text: str) -> set[str]:
    return set(re.findall(r'\bname:\s*"(ep[0-9][a-z0-9]*)"', text))


def parse_readme_keys(text: str) -> set[str]:
    section = re.search(r"^### Available Settings\s*$(.*?)(?=^### |\Z)",
                        text, re.M | re.S)
    if section is None:
        raise ValueError("README has no '### Available Settings' section")
    return set(re.findall(r"^- `([a-z_]+)`:", section.group(1), re.M))


def parse_readme_differences(text: str) -> str:
    section = re.search(r"^## Known Differences\s*$(.*?)(?=^## |\Z)",
                        text, re.M | re.S)
    if section is None:
        raise ValueError("README has no '## Known Differences' section")
    return section.group(1)


def parse_options(text: str) -> set[str]:
    block = re.search(r"const OPTIONS:[^=]*=\s*&\[(.*?)\n\];", text, re.S)
    if block is None:
        raise ValueError("config.rs has no OPTIONS array")
    return set(re.findall(r'\(\s*"([a-z_]+)"\s*,', block.group(1)))


def parse_doc_flags(text: str) -> set[str]:
    return set(re.findall(r"(--[a-z0-9][a-z0-9-]*)", text))


def parse_code_flags(sources: list[str]) -> set[str]:
    out: set[str] = set()
    for src in sources:
        out.update(re.findall(r'"(--[a-z0-9][a-z0-9-]*)"', src))
    return out


def check(root: pathlib.Path, overrides: dict[str, str] | None = None,
          tracked: list[str] | None = None) -> list[str]:
    """Compare the documents. `overrides` / `tracked` let the self-test feed
    drifted text and a fake git index through the very same comparisons a real
    run uses, instead of reimplementing them in the test."""
    problems: list[str] = []

    def text(rel: str) -> str:
        if overrides is not None and rel in overrides:
            return overrides[rel]
        return read(root, rel)

    def report(name: str, items: list[str]) -> None:
        for item in items:
            problems.append(f"{name}: {item}")

    # 1. milestone status. Guard against a silent column shift: if both tables
    # ever gain a column, cols[4] could land on the same wrong column in both
    # and the comparison would go green without checking any state at all.
    status = parse_milestones(text("STATUS.md"))
    plan = parse_milestones(text("plan/PLAN.md"))
    valid = {"Done", "In progress", "Pending", "Next"}
    for label, table in (("STATUS.md", status), ("plan/PLAN.md", plan)):
        for m, word in sorted(table.items()):
            if word not in valid:
                report("milestones", [f"{label} {m}: unrecognised state {word!r} "
                                      f"(table columns may have shifted)"])
    if not status or not plan:
        report("milestones", ["could not parse one of the two tables"])
    else:
        for m, want in sorted(status.items()):
            got = plan.get(m)
            if got is None:
                report("milestones", [f"{m} missing from plan/PLAN.md"])
            elif got != want:
                report("milestones", [f"{m}: STATUS.md says {want!r}, PLAN.md says {got!r}"])

    # 2. jump names (both directions: an extra name in either file is a bug)
    doc_jumps = parse_jump_table(text("run.md"))
    code_jumps = parse_jump_source(
        text("dino-rs/crates/dino-game/src/jumps.rs"))
    if not doc_jumps or not code_jumps:
        report("jumps", ["could not parse the jump table or JUMPS"])
    else:
        report("jumps", [f"in run.md but not jumps.rs: {n}"
                         for n in sorted(doc_jumps - code_jumps)])
        report("jumps", [f"in jumps.rs but not run.md: {n}"
                         for n in sorted(code_jumps - doc_jumps)])

    # 3. config keys
    readme_text = text("dino-rs/README.md")
    readme_keys = parse_readme_keys(readme_text)
    option_keys = parse_options(
        text("dino-rs/crates/dino-game/src/game/flow/config.rs"))
    report("config", [f"in README but not OPTIONS: {k}"
                      for k in sorted(readme_keys - option_keys)])
    report("config", [f"in OPTIONS but not README: {k}"
                      for k in sorted(option_keys - readme_keys)])

    # 4. CLI flags named in the docs must be parsed by some crate
    doc_flags = parse_doc_flags(text("run.md") + readme_text)
    crate = root / "dino-rs" / "crates"
    sources = [p.read_text(encoding="utf-8")
               for p in crate.rglob("*.rs") if p.is_file()]
    code_flags = parse_code_flags(sources)
    report("flags", [f"documented but not parsed: {f}"
                     for f in sorted(doc_flags - code_flags - CARGO_FLAGS)])

    # 6. a fixed difference must not be advertised to players as current
    differences = parse_readme_differences(readme_text)
    for marker, source in GONE_MARKERS:
        if marker in differences:
            report("known-differences", [f"README still lists {marker!r} ({source})"])

    # 5. no ROM-derived data in git (M10-26)
    if tracked is None:
        tracked = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                                 text=True, check=True).stdout.splitlines()
    for path in tracked:
        if path.lower().endswith(ROM_SUFFIXES) or path.startswith(ROM_PREFIXES):
            problems.append(f"git-leak: ROM-derived file is tracked: {path}")

    return problems


FILES = (
    "STATUS.md",
    "plan/PLAN.md",
    "run.md",
    "dino-rs/README.md",
    "dino-rs/crates/dino-game/src/jumps.rs",
    "dino-rs/crates/dino-game/src/game/flow/config.rs",
)


def self_test(root: pathlib.Path) -> list[str]:
    """Feed one drifted input per check through `check` itself. A check that
    cannot catch its own drift is worse than no check: it would look green."""
    base = {rel: read(root, rel) for rel in FILES}
    failures: list[str] = []

    def run_case(name: str, needle: str, overrides: dict[str, str],
                 tracked: list[str] | None = None) -> None:
        got = check(root, overrides=overrides, tracked=tracked if tracked is not None else [])
        if not any(needle in p for p in got):
            failures.append(f"{name}: drift was NOT caught (problems={got})")

    clean = check(root, overrides=base, tracked=[])
    if clean:
        failures.append(f"clean baseline is not clean: {clean}")

    # 1. the short map left at "Pending" while STATUS.md says Done
    run_case("milestones", "milestones", {
        **base, "plan/PLAN.md": base["plan/PLAN.md"].replace(
            "| Done (2026-10-13) |", "| Pending |", 1)})

    # 2. a jump point documented but removed from the source
    run_case("jumps", "jumps", {
        **base, "dino-rs/crates/dino-game/src/jumps.rs":
            base["dino-rs/crates/dino-game/src/jumps.rs"].replace(
                'name: "ep8a3"', 'name: "ep8a3_gone"', 1)})

    # 3. a config key renamed in OPTIONS but not in the README
    run_case("config", "config", {
        **base, "dino-rs/crates/dino-game/src/game/flow/config.rs":
            base["dino-rs/crates/dino-game/src/game/flow/config.rs"].replace(
                '("sound", 1,', '("sound_level", 1,', 1)})

    # 4. a flag documented but never parsed
    run_case("flags", "flags", {
        **base, "run.md": base["run.md"] + "\n- `--no-such-flag`: drift probe.\n"})

    # 5. a difference final.txt marks GONE advertised again
    run_case("known-differences", "known-differences", {
        **base, "dino-rs/README.md": base["dino-rs/README.md"].replace(
            "## Known Differences",
            "## Known Differences\n\n- **Fessenden with three heroes.** Drift probe.\n", 1)})

    # 7. both tables gain a column at once: the fixed column index now lands on
    # the same Hours value in both, so the naive comparison would go GREEN.
    # The state-word guard must catch it instead.
    shift = lambda t: re.sub(r"^(\| M\d+ \|)", r"\1 X |", t, flags=re.M)
    run_case("column shift", "unrecognised state", {
        **base,
        "STATUS.md": shift(base["STATUS.md"]),
        "plan/PLAN.md": shift(base["plan/PLAN.md"]),
    })

    # 6. a ROM-derived file tracked in git
    run_case("git-leak", "git-leak", base,
             tracked=["re/out/assets/anims/hero_jack/x.gif"])

    return failures


USAGE = """usage: check_docs.py [--self-test]

  (no args)    run the 6 static doc/code consistency checks
  --self-test  verify a clean baseline and that 7 deliberate drifts are caught
  -h, --help   show this message
"""

# Only these are accepted. An unknown flag must not silently fall through to a
# normal run: a typo like `--slft-test` would then print "6/6 passed" and look
# as if the self-test had succeeded.
VALID_ARGS = {"--self-test", "-h", "--help"}


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    argv = sys.argv[1:]
    unknown = [a for a in argv if a not in VALID_ARGS]
    if unknown:
        print(f"check_docs: unknown argument(s): {' '.join(unknown)}\n{USAGE}",
              file=sys.stderr)
        return 2
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE, end="")
        return 0
    if "--self-test" in argv:
        try:
            failures = self_test(root)
        except (FileNotFoundError, ValueError) as exc:
            print(f"check_docs --self-test: cannot run: {exc}", file=sys.stderr)
            return 2
        if failures:
            for f in failures:
                print(f"  - {f}", file=sys.stderr)
            return 1
        print("check_docs --self-test: clean baseline + 7/7 drift cases caught")
        return 0
    try:
        problems = check(root)
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"check_docs: cannot run: {exc}", file=sys.stderr)
        return 2
    if problems:
        print(f"check_docs: {len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("check_docs: 6/6 checks passed "
          "(milestones, jumps, config keys, CLI flags, known differences, git leak)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
