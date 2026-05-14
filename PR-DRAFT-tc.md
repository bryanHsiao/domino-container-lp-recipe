# PR Draft — Add Traditional Chinese LP Support

> **Status: draft, not yet submitted.** Target: `HCL-TECH-SOFTWARE/domino-container`. This file is the proposed PR description, ready to convert into a `git format-patch` series + GitHub PR when timing/maintainer-bandwidth allows.

---

## Suggested PR title

```
Add Traditional Chinese (TC) Language Pack support to build.sh menu (closes #55)
```

## Body

### Summary

Adds **Traditional Chinese (TC)** Language Pack support to `build.sh menu` and `install_domino.sh`. Follows the same pattern @Daniel-Nashed established when adding the original 6 LPs (DE/ES/FR/IT/NL/JA) in 2022.

### Why

Issue [#55](https://github.com/HCL-TECH-SOFTWARE/domino-container/issues/55) asked about LP support beyond the original 6. In that discussion, @Daniel-Nashed said:

> "The right way would be to add it to the software file, but then we would need to support all the languages..."

This PR provides the structural hooks for TC. It's deliberately minimal — it does not commit maintainers to ongoing LP-specific data maintenance. Future LP additions (SC, KO, …) are then one-line additions to `software.txt` plus a corresponding `build.sh` entry following the same pattern.

### Changes

**1. `build.sh`** — 4 surgical edits, same pattern as the existing JA case:

- `LP_TC="Traditional Chinese"` variable added in `get_language_pack_display_name()` and `select_language_pack()`
- `TC)` case in the display-name `case` statement
- `print_lp "TC" "$LP_TC"` in the menu print list
- `t)` keypress case mapping to `SELECT_DOMLP_LANG=TC`

**2. `dockerfiles/install_dir_domino/install_domino.sh`** — 1 case mapping inserted after the `DOMLP_LANG_LCASE=...` assignment:

```bash
# Map non-ISO short codes to the values LNXDomLP expects internally.
# LNXDomLP strings reveal: LangCodeList("zh-TW") = "TC"
case "$DOMLP_LANG_LCASE" in
  tc) DOMLP_LANG_LCASE=zh-TW ;;
  sc) DOMLP_LANG_LCASE=zh-CN ;;  # included as future-proofing for SC; not tested
esac
```

This is needed because TC/SC short codes aren't ISO 639-1 standard, while LNXDomLP's internal `LangCodeList` uses `zh-TW`/`zh-CN`. Without the mapping, the silent install runs but `LPLog.txt` isn't written, and the build fails with `Cannot find LPLog.txt in /opt/hcl/domino`. (Discovered via `strings LNXDomLP | grep LangCodeList` after extracting the LP tar.)

**3. `software/software.txt` and `dockerfiles/install_dir_common/software.txt`** — TC manifest entry in both files. (The two files have identical content but serve different purposes: host-side pre-build sanity check vs. container-side `install_domino.sh` lookup.)

The SHA256 in the entry is from my own tar; maintainers should regenerate from HCL's canonical tar if there's any discrepancy. `CHECK_HASH` defaults to empty, so this doesn't affect the sanity check.

### Testing

Tested combination:

- Domino 14.5.1 (from FlexNet)
- Ubuntu 24.04.4 LTS on WSL2 (Windows 11)
- Docker 29.4.3
- `dominoctl` (Nash!Com) 1.5.5
- Upstream commit: 4734801 ("Add Domino 12.0.2FP8")

Verified:

- [x] `./build.sh menu` → press L → submenu shows `(TC) Traditional Chinese`
- [x] `./build.sh menu` → press L → press t → main menu shows `(L) Language Pack [X] 14.5.1`
- [x] `./build.sh domino 14.5.1 -restapi=1.1.7 -leap=1.1.10 -domlp=TC` completes in ~5 minutes
- [x] Image label `DominoContainer.addons` includes `languagepack=TC`
- [x] 9 `zh-tw` resource directories in image (XSP UI themes)
- [x] LP install log shows `Selected Language Packs are successfully installed`
- [x] Fresh OneTouch Setup produces a `names.nsf` with Chinese form/view labels (server console.log contains e.g. `Event: Creating the Domino 網域監督 (11) database.`)
- [x] HTTP server starts and serves `/homepage.nsf`

### Known limitations (not addressed in this PR)

1. **SC mapping included but unverified**: the `sc → zh-CN` line in the case statement is best-guess symmetry, not actually tested with a SChinese tar. Maintainers may want to remove it or verify before merging. If left in, it's harmless to TC.

2. **No SC/KO/etc. `software.txt` entries**: this PR adds only TC entries. SC/KO follow-up PRs are trivial.

3. **Existing `/local/notesdata` won't pick up the new LP**: this is the limitation @Daniel-Nashed described in #55 ("no concept adding any data after initial configuration"). A user who built a non-LP image, did setup, then rebuilds with LP, will see existing `.nsf` files stay English because Domino's entrypoint detects `Data already installed for 14050100` and skips template deployment. **This PR doesn't change that behavior.** A separate PR would be needed for that (out of scope here).

### Closes

Closes #55 partially — addresses the structural ask for LP menu extensibility (adding TC, with the mapping infrastructure SC/KO can use), but not the post-install template-update gap.

### Companion materials

- Community recipe (this PR's source, plus apply-script for users who can't wait for upstream): [`bryanHsiao/domino-container-lp-recipe`](https://github.com/bryanHsiao/domino-container-lp-recipe)
- Full WSL2 SOP including this integration: [`bryanHsiao/domino-container-wsl2-sop`](https://github.com/bryanHsiao/domino-container-wsl2-sop)
