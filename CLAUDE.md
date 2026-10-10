# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data mirror for the Taigi entries of the Taigi Wiktionary (https://zh-min-nan.wiktionary.org/). Part of the ChhoeTaigi project, and the Wiktionary twin of `WikipediaPehoejiDataMirror`. The repo downloads the monthly `pages-articles.xml.bz2` dump from https://dumps.wikimedia.org/zh_min_nanwiktionary/, reads the wikitext of every main-namespace page, keeps the Taigi entries — pages titled in Pe̍h-ōe-jī with Taigi content, and Hanji pages whose `*臺灣話：` line gives a reading — and converts them into one CSV+JSON table with the ChhoeTaigi database's own column names, hosted via GitHub Pages.

Licensed **CC BY-SA 4.0**, as Wiktionary is: credit Wiktionary, share alike.

It replaces the Wiktionary half of `ParseWikipediaPehoejiPanAllTitlesInNamespace0` (`src/main/kotlin/wiktionary/Main2.kt`, run once on the 2024-10-20 all-titles dump), whose 1,481 title-only rows became the `Wiktionary (Wiki詞典)` rows of `SoanntengBunjiMuitheSekin` in `ChhoeTaigiPlusWebsite/database_src`.

## Commands

```bash
# Run the full update pipeline (downloads the ~3.6 MB dump, converts, checks
# for changes via SHA256 of the published CSV+JSON, publishes a version)
cd script && python update_data.py

# Iterate without downloading, against a local dump. It must keep its dated
# name (the manifest records the dump URL built from it), as in every tangloo/.
cd script && python update_data.py --dump ../public/{version}/tangloo/zh_min_nanwiktionary-YYYYMMDD-pages-articles.xml.bz2

# Force a new version directory even when the output is unchanged — and
# publish even when counts fell more than 5% since the last version, or the
# dump is older than the published one
cd script && python update_data.py --force

# Run only the conversion
cd script && python convert_entries.py ../public/{version}/tangloo/zh_min_nanwiktionary-YYYYMMDD-pages-articles.xml.bz2 /tmp/out/bunji
```

Dependencies: pure Python stdlib (no `pip install` needed). A full run takes a few seconds plus the download.

### Verifying a change

There is no test suite. The pipeline *is* the check: run it and read
`public/{version}/WiktionaryTaioanoeDataQuality.md`.

- **Selection check.** `contains_poj()` is shared with the Wikipedia mirror and tested on the title with spaces as `_`, so the 2024 Kotlin output (`../ParseWikipediaPehoejiPanAllTitlesInNamespace0/zh_min_nanwiktionary-20241020-all-titles-in-ns0-output.csv`, 1,481 rows) must still account exactly: matched on `LaigoanBangchi`, 706 identical, 10 corrected (`o·` → `o͘`), 181 redirects, 493 without Taigi content, 47 index pages, 44 no longer in the dump. A change that moves rows between these lines must be meant.
- **Row checks.** `人` → `jîn`, others `lîn/lâng(替)`; `水` → `suí`, others `suí(文)/chúi` (a first reading with a note is repeated); `錢` → `chîⁿ`, others `chiân(文)/chhiân(俗音)`; `入學` → `ji̍p-o̍h`, others `li̍p-o̍h/ji̍p-ha̍k(又唸作)/li̍p-ha̍k(又唸作)`; `落去` → `lo̍h--khì`, others `loeh`; `陳` → `tân` (from `{{zh-pron|mn=tân/tîn}}`); `莊` → `Chng` (from the Mandarin entry's `* Bân-lâm-gí:` line); `日本` → others `Ji̍t-pún(zz,kh)/Li̍t-pún(xm,qz,tp)`. `A-chiu` → `亞洲`, `Bêng-sû`, EngBun `Asia`, HoaBun `亞洲`, JitBun `アジア`; `lâng` → `人/儂/聾`; `só·-í` → `só͘-í`, `soo2-i2`. `ant`, `sin`, `American black bear` and the Malay `gua` (a `*Hō-ló-oē:` translation line under a Latin title) must be dropped as "no Taigi content"; `hîm` (`== Hō-ló-oē ==`) kept; `Sek-ín:…` dropped as index pages.
- **Report.** "Reading lines with text that could not be read" should stay at 0; "Readings not in Pe̍h-ōe-jī spelling" at ~27, all genuine KPL spellings or slips. In section 1 the dropped-page counts plus rows must add up to the pages in the dump.
- A second run with unchanged data must reuse the existing version directory.

## Architecture

### Data Pipeline (`script/`)

1. **`update_data.py`** — Main entry point. Verifies `README.md`/`index.md` are in sync, reads `latest/…-pages-articles.xml.bz2-rss.xml` to resolve the dated dump run, downloads it, builds into a staging directory, compares the SHA256 of the published table (CSV and JSON) against `public/manifest.json`, and only then moves it into a timestamped version directory and writes the manifest. Same shape as the Wikipedia mirror's, without the API stage.

2. **`convert_entries.py`** — Streams the XML (`ElementTree.iterparse`), classifies each page (`page_kind`), parses readings (`page_readings`, `parse_reading_line`), Hanji, part of speech, definitions and translations (`page_entry`), builds the rows, sorts them by `PojUnicode` (`collation_key`) and writes `bunji/WiktionaryTaioanoe.{csv,json}` plus the report.

3. **`poj_text.py`** — The Pe̍h-ōe-jī machinery ported verbatim from `WikipediaPehoejiDataMirror/script/convert_titles.py`: `POJ_UNICODE_REGEX`/`contains_poj`, `poj_unicode_to_input`, `TEXT_CORRECTIONS`, attested hyphenation, `title_text`. Keep it in step with the sibling; do not "fix" the regex (see its CLAUDE.md).

### Key design decisions

- **Content, not just titles.** The Wikipedia mirror publishes titles; here the dump is 3.6 MB and the entries hold Hanji ↔ Pe̍h-ōe-jī pairs, so the wikitext is read. Hanji pages (15,700, imported from the Ministry of Education dictionary) are regular; Pe̍h-ōe-jī pages (785) are hand-written in several layouts, read by heading (`heading_key`, `POS_HEADINGS`, `HANJI_HEADINGS`, `TRANSLATION_HEADINGS`). What is not read is counted in the report (`skipped_headings`) rather than guessed.

- **One row per page.** `LaigoanBangchi` is unique. Several readings go to `PojUnicodeOthers` in KauiokPooSutian's `reading(note)/reading` format — the same MOE data, the same shape in the database. A page that is several homophonous words (`ka`: 家/鳩/鉸/加) keeps one row with its Hanji, definitions and translations joined; one row per sense was considered and rejected to keep the link unique.

- **Selection is the 2024 rule plus "has Taigi content".** `contains_poj` matches `ant`, `net`, `American black bear` (`r` counts as a vowel); on a dictionary with 5,000 foreign entries that would publish English as Taigi, so a Pe̍h-ōe-jī title needs a Taigi language heading (`TAIGI_LANGUAGE`), a part-of-speech or translation heading at level 2, a Taigi category, a nan-* template or a reading. The 493 titles this drops from the 2024 import are all foreign words, letters or index pages; they are listed in the report.

- **Readings come from four places, in order.** `*臺灣話：` lines; else `{{zh-pron|mn=…}}` (the English Wiktionary's template, dialect codes kept as the note); else, under a Hanji title only, a `* Bân-lâm-gí:` line (the surname pages are Mandarin entries whose Taigi reading sits in their translation table — under a Latin title, `gua`, the same line is a translation); else `{{nan-pron}}`. Plus `poj=`/`vary=` of nan-* templates always. Readings of other dialects (泉州話, 漳州話…) are never published — the repo is `Taioanoe`.

- **Redirects are not rows.** The dump marks them, their target carries the content, and ASCII-tone-number redirects (`A-la-pek-gi2`) are reachable through `PojInput` anyway. This drops 181 rows of the 2024 import.

- **A failed run's report is kept under `temp_update_failed/report-{dump_date}/`**, named by dump run, so a later success of another run neither removes nor replaces it; `clear_failed` removes the report of the run it supersedes. A failure after the build moved into its version directory hands the report back as well as the download.

- **Change detection, staging, count-drop refusal, dated URLs** — as in the Wikipedia mirror: the table's hash decides, nothing under `public/` is touched until conversion succeeded, a >5% drop in `WATCHED_COUNTS` refuses to publish without `--force`, and a run that cannot name a dated dump does not publish.

### Non-obvious invariants

- **`contains_poj` is tested on `title.replace(" ", "_")`.** The all-titles dump writes spaces as `_`, and the 2024 rule splits on `_` but not on spaces; XML titles have spaces. Without the replace, `Tiong-hôa Bîn-kok` still matches but `American black bear` does not, and the comparison with the 2024 import no longer accounts for every row.

- **`heading_key` keys Hanji-only headings through `HAN_HEADINGS`.** Every other heading is keyed by its Latin letters with Hanji stripped (`Bêng-sû 名詞` → `bengsu`), so a heading that is Hanji alone (`意思`, `翻譯`) would key to `""`. Add new Hanji headings there, not to `POS_HEADINGS`.

- **A parenthesis in a reading line is a note unless it holds only links.** `[[lâi-khì]]([[laih]], [[la̋i]])` lists contracted readings; `[[ió-bih]]（日語[[予備]]借音）` is a note containing a link. `LINKED_PARENTHESIS` matches the first shape only. Loosen it and the note becomes an unreadable "reading" (it was the one unparsed line before the fix).

- **"又唸作" is a separator, not text — outside a parenthesis.** `[[ji̍p-o̍h]]/[[li̍p-o̍h]] 又唸作 [[ji̍p-ha̍k]]` — split only on punctuation, `li̍p-o̍h ji̍p-ha̍k` becomes one reading. Parentheses are stashed whole (innermost first) before the split, so `（又唸作 b）` stays a note and a separator inside a note never cuts the line.

- **`_hanji_from_line` strips a label only when it holds no link or Hanji.** `* Chiàⁿ-jī: [[藥]]` loses its label; `* [[毋]][[通]]: chù` keeps its Hanji. A greedy strip-to-colon lost the Hanji of the second shape.

- **`counts` is a Counter: derived totals are assigned, never `update()`d.** `Counter.update(mapping)` adds, so a key the page loop had incremented would be doubled in the report and manifest.

- **`pojt=` is checked only on Pe̍h-ōe-jī pages.** On a Hanji page with a `ts` template, `pojt` lists the readings in its own order (`lang5,jin5`), which is not a disagreement with `PojInput`.

- **The first reading's note is kept by repeating the reading in `PojUnicodeOthers`.** `葉` → `hio̍h` / `hio̍h(替)/ia̍p`. KauiokPooSutian never annotates its main reading; Wiktionary does, 348 times. Dropping the note silently was rejected; a column for it does not exist in the database.

- **Translations are read from the Taigi section only** (`taigi_sections`): the same page can hold an English entry with its own translation table. A page with no language heading at all is one entry; one with foreign headings only keeps its preamble and the level-2 sections that name no language.

- **`HoaBun` strips parentheses and keeps the first form only; `EngBun` keeps everything.** Chinese and Japanese lines parenthesise romanisations (`(mǎyǐ)`); English lines parenthesise glosses (`admit (into membership)`). Chinese lines list the traditional and the simplified form, and the repo has no conversion table, so `HoaBun` is the first form listed (decided 2026-10-10; it also cuts `[[假使]], [[假如]]` to `假使`).

### Downstream

`ChhoeTaigiDatasetGenerator` has a `WiktionarySekinMapper` (`manifest/sources.yaml`, code `WiktionarySekin`) that reads the all-titles dump directly, applies no Pe̍h-ōe-jī filter and gives titles only. Pointing it at this mirror's CSV is the intended follow-up; it recomputes `PojInput` and the KPL columns itself.

### Data Layout (`public/`)

```
public/
  manifest.json                         # Latest version, source dump, per-file SHA256, counts
  {YYYYMMDD-HHMMSS}/                    # Timestamped version directory
    WiktionaryTaioanoeDataQuality.md    # Data-quality report
    WiktionaryTaioanoeDataQuality.json  # Same, machine-readable, with the full lists
    bunji/
      WiktionaryTaioanoe.csv/.json      # one row per Taigi entry
    tangloo/                            # The dump and its Last-Modified — gitignored
```

### Hosting

- `index.md` is the GitHub Pages landing page
- `.nojekyll` disables Jekyll processing

## Important Rules

- **`README.md` and `index.md` must stay in sync.** They have identical content. `update_data.py` aborts before any network work if they differ. Fix with `cp README.md index.md`. Update the version ID, dates and counts in both after each new version.
- **`manifest.json` keys files by path relative to the version directory** (`bunji/WiktionaryTaioanoe.csv`), skipping `tangloo/`.
- **Never commit the dump.** `public/*/tangloo/` is gitignored.
- **Never correct `LaigoanBangchi`; never correct a reading or title silently.** Every corrected value is listed in the report; a reading that is not Pe̍h-ōe-jī is published as written and listed.
- **Pure stdlib only.**

## Terminology (Taigi)

- **Taigi** — the language. Never "Taiwanese Southern Min", "Holo" or "Hokkien" in prose. `zh-min-nan` / `zh_min_nanwiktionary` appear only as upstream identifiers; `Tâi-oân-ōe`, `Bân-lâm-gí` and `閩南語` only as the wiki's own headings.
- **Roman Orthography** — never "Romanization".
- **Pe̍h-ōe-jī (POJ)** — the Taigi Roman-script Orthography.
- **KPL (Kàu-io̍k Pō͘ Lô-má-jī)** — the Taigi Latin-script Orthography. Not produced here; never "Tâi-lô" or "TL".
- **Hàn-jī** (漢字) — Chinese characters. Column `HanLoTaibunPoj`.
- **bûn-jī** (文字) — text data. Directory `bunji/`.
- **táng-ló͘** (檔路) — download. Directory `tangloo/`.
- **Eng-bûn, Hôa-bûn, Ji̍t-bûn** (英文, 華文, 日文) — English, Chinese, Japanese. Columns `EngBun`, `HoaBun`, `JitBun`.
