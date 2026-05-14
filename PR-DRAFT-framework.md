# PR Draft (Speculative) — Refactor LP Menu to Be Registry-Driven

> **Status: speculative; submit only after PR-DRAFT-tc.md is accepted.** This proposes a larger refactor that would make adding future LPs (SC/KO/TH/…) a one-line change to a registry file, eliminating the need for community recipes like this one.

---

## Suggested PR title

```
Refactor build.sh LP menu and install_domino.sh to be registry-driven
```

## Body

### Motivation

The current `build.sh` hardcodes the 6 supported LPs (DE/ES/FR/IT/NL/JA) in two places (`select_language_pack` and `get_language_pack_display_name`), each requiring 4 surgical edits per language. The LP installer code derivation in `install_domino.sh` assumes the lowercased short code matches the installer's internal `LangCodeList` value — which is true for the 6 supported languages but not for Chinese variants.

This makes adding a new LP (TC, SC, KO, …) a ~5-edit cross-file change. PR #N (the TC-specific PR) shows the pattern. If maintainers prefer not to do this 5-edit dance every time someone asks for a new LP, a registry-driven approach would let new LPs be added by appending one entry to a list.

### Proposed shape

Add a file `dockerfiles/install_dir_common/language-packs.txt`:

```
# Format: code|display_name|keypress|installer_code
# (installer_code is what LNXDomLP's LangCodeList expects)
DE|German|d|de
ES|Spanish|e|es
FR|French|f|fr
IT|Italian|i|it
NL|Dutch|n|nl
JA|Japanese|j|ja
TC|Traditional Chinese|t|zh-TW
SC|Simplified Chinese|s|zh-CN
KO|Korean|k|ko
TH|Thai|h|th
```

In `build.sh`:

- `select_language_pack()` reads this file and dynamically prints each `print_lp` line + builds the keypress `case`
- `get_language_pack_display_name()` likewise becomes data-driven

In `install_domino.sh`:

- After deriving `DOMLP_LANG_LCASE`, look it up in language-packs.txt to find the actual `installer_code`. No per-language case mapping needed.

### Benefits

- Adding a new LP becomes: append one line to `language-packs.txt`. No `build.sh` / `install_domino.sh` edits.
- Maintainer doesn't need to verify the installer_code themselves — community PRs to `language-packs.txt` get reviewed for correctness of the single line.
- Existing `software.txt` semantics unchanged (still per-LP-per-version entries).

### Trade-offs

- Slightly more complex `build.sh` (reads from a manifest instead of inlining), but the code becomes shorter overall once the dynamic generation replaces the hardcoded 6.
- New file (`language-packs.txt`) to ship in the dockerfiles directory.
- Existing users who customized the hardcoded list (rare) need to migrate.

### Testing

Would extend the testing matrix from PR #N (TC-specific) to also cover SC/KO/TH on `language-packs.txt`-driven menu. Same `Selected Language Packs are successfully installed` log signal applies.

### Why a separate PR

Keeping this separate from the TC PR allows:
- TC PR is small (~5 edits), easy to review and merge
- This refactor PR can be reviewed at maintainer's pace without blocking TC
- If maintainer prefers to keep the hardcoded approach (legitimate choice), TC still lands

### Companion materials

- TC-specific PR: [link to PR-DRAFT-tc.md PR when submitted]
- Community recipe that implements the registry approach already: [`bryanHsiao/domino-container-lp-recipe`](https://github.com/bryanHsiao/domino-container-lp-recipe)

---

**Note to recipe authors**: this draft is speculative. Don't submit unless PR-DRAFT-tc is accepted first, and Daniel signals openness to refactoring. Otherwise this looks like over-engineering a feature he doesn't prioritize.
