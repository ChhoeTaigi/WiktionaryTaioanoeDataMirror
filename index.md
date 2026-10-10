# WiktionaryTaioanoeDataMirror

Data mirror for ChhoeTaigi WiktionaryTaioanoe. This site provides direct access to every Taigi entry in the Taigi Wiktionary ([zh-min-nan.wiktionary.org](https://zh-min-nan.wiktionary.org/)): each word in Pe̍h-ōe-jī with its tone-number input form, its Hanji, its further readings, part of speech, definitions, English / Chinese / Japanese equivalents, and a link to the page. The files are hosted on GitHub Pages for easy access.

## Chu-liāu Pán-koân

版權聲明

- 資料授權：[CC BY-SA 4.0「姓名標示－相同方式分享」授權](https://creativecommons.org/licenses/by-sa/4.0/deed.zh-hant)
- 資料來源：Wiktionary (Wiki詞典) contributors, <https://zh-min-nan.wiktionary.org/>

Wiktionary content is licensed CC BY-SA 4.0. If you redistribute these tables or anything built from them, **credit Wiktionary** and **release your derivative under the same licence**.

## Latest Version

- **Version ID:** `20261010-151645`
- **Last Updated:** 2026-10-10
- **Source dump:** `zh_min_nanwiktionary-20261001-pages-articles.xml.bz2` (dump run 2026-10-01)
- **Coverage:** 16,512 rows out of 23,024 main-namespace pages: 787 pages titled in Pe̍h-ōe-jī and 15,725 pages (nearly all titled in Hanji) with a Taigi reading; 15,988 rows with Hanji, 2,952 with a definition, 228 with an English, Chinese or Japanese equivalent

You can check [**manifest.json**](./public/manifest.json) for the latest version information programmatically. It records `last_updated`, `latest_version_dir`, the source dump URL and date, per-file SHA256 hashes, and row counts.

## Accessing Files

The files are organized by version. Once updated, the latest files will be in `public/{version}/`.

```
bunji/                                # 文字
  WiktionaryTaioanoe.csv/.json          # one row per Taigi entry
WiktionaryTaioanoeDataQuality.md/.json  # counts and findings for this version
```

### `WiktionaryTaioanoe` — one row per Taigi entry

16,512 rows, one per Wiktionary page that is a Taigi entry (see "Which pages are entries" below).

* **CSV:** `https://chhoetaigi.github.io/WiktionaryTaioanoeDataMirror/public/{version}/bunji/WiktionaryTaioanoe.csv`
* **JSON:** `https://chhoetaigi.github.io/WiktionaryTaioanoeDataMirror/public/{version}/bunji/WiktionaryTaioanoe.json`
* **Columns:** `PojUnicode, PojInput, PojUnicodeOthers, PojInputOthers, HanLoTaibunPoj, Hunlui, KaisoehPoj, KaisoehHanLoPoj, EngBun, HoaBun, JitBun, LaigoanBangchi`

| Column | Description | Rows filled |
|--------|-------------|-------------|
| `PojUnicode` | The word in Pe̍h-ōe-jī: the page title (`A-chiu`), or the first reading on a Hanji page's `*臺灣話：` line (`jîn` for `人`) | 16,512 |
| `PojInput` | The same in tone-number input form, e.g. `jin5` | 16,512 |
| `PojUnicodeOthers` | Further readings, each with its note in parentheses, joined with `/`: `lîn/lâng(替)` for `人`, `chiân(文)/chhiân(俗音)` for `錢` | 3,184 |
| `PojInputOthers` | The same in input form: `lin5/lang5(替)` | 3,184 |
| `HanLoTaibunPoj` | The Hanji: the page title of a Hanji page, or what a Pe̍h-ōe-jī page gives in its nan-* template (`tas=手`) or `Hàn-jī` section; several forms joined with `/` (`人/儂/聾` for `lâng`) | 15,988 |
| `Hunlui` | Part of speech as the page gives it: `Bêng-sû`, `Tōng-sû`, `Hêng-iông-sû`… | 711 |
| `KaisoehPoj` | Definitions written in Pe̍h-ōe-jī, one per line | 741 |
| `KaisoehHanLoPoj` | Definitions written in Hanji (the `意思` section of a Hanji page), one per line | 2,211 |
| `EngBun` | English equivalents from the page's translation table, e.g. `person, humanity, human race, mankind` | 208 |
| `HoaBun` | Chinese equivalent: the first form the page's line lists, e.g. `螞蟻` (the line reads `[[螞蟻]], [[蚂蚁]] (mǎyǐ)`) | 188 |
| `JitBun` | Japanese equivalents, e.g. `蟻` | 178 |
| `LaigoanBangchi` | Link to the page, e.g. `https://zh-min-nan.wiktionary.org/wiki/人` | 16,512 |

The column names are the ones the ChhoeTaigi database uses for these rows (dataset `SoanntengBunjiMuitheSekin`, 線頂文字媒體索引, `LaigoanMia` = `Wiktionary (Wiki詞典)`), so the table can be loaded without renaming. `PojUnicodeOthers` follows the format KauiokPooSutian uses for the same Ministry of Education data (`chi̍t(替)`, several joined with `/`).

CSV is UTF-8 **with BOM** (so Excel auto-detects the encoding), every field quoted, with a header row (~2 MB). JSON is a UTF-8 array with one record per line (~5 MB).

## Which pages are entries, and how they are rendered

The Taigi Wiktionary writes two kinds of Taigi entry:

- **Pages titled in Pe̍h-ōe-jī** (`A-chiu`, `chhiú`, `bah-chàng`), written in Taigi under a `Tâi-oân-ōe` or `Bân-lâm-gí` heading. A title counts as Pe̍h-ōe-jī when any of its parts — split on `-`, `_`, `(`, `)` and spaces — is a single Pe̍h-ōe-jī syllable, the rule ChhoeTaigi has used since its first Wiktionary import. Because that rule also matches `ant`, `sin`, `net` and many words of other languages, a page is kept only when it has Taigi content: a Taigi language heading, a Taigi category, a nan-* template or a `*臺灣話：` reading. Dropped titles are listed in the report.
- **Pages titled in Hanji** (`人`, `亞洲`, `塭仔`), 15,700 of them imported from the Ministry of Education dictionary (臺灣閩南語常用詞辭典) with their Taiwanese reading on a `*臺灣話：` line. The first reading is `PojUnicode`, the rest `PojUnicodeOthers`; the title is `HanLoTaibunPoj`. A few give the reading in a `{{zh-pron|mn=…}}` or `{{nan-pron}}` template, or — the surname pages, `莊` → `Chng` — on the `Bân-lâm-gí:` line of a Mandarin entry's translation table; those are read too. That last line is read only under a Hanji title: on a Malay or English page (`gua`) it is a translation, not a reading.

Redirects are not rows: their target is. Index and appendix pages (`Sek-ín:…`, `Pe̍h-ōe-jī Sek-ín A`) and entries of other languages are dropped.

- **`PojUnicode`.** Made as good as possible for finding by Pe̍h-ōe-jī, since ChhoeTaigi searches this column; `LaigoanBangchi` keeps the exact page. The dot of o͘ typed as `·` is restored (`só·-í` → `só͘-í`), as in the Wikipedia mirror; every corrected value is listed in `WiktionaryTaioanoeDataQuality.md`/`.json`.
- **`PojInput`.** Each tone mark is removed and its number appended to the word: acute 2, grave 3, circumflex 5, macron 7, vertical line 8, breve or double acute 9. `o͘` → `oo`, `ⁿ` → `nn`. A word with two tone marks is left as written and listed in the report (none in this version). A caron is not read as a tone mark.
- **Readings and their notes.** The `*臺灣話：` line annotates readings: `文` literary reading, `替` the Hanji is a substitute character for this reading, `俗`/`俗音` popular pronunciation, `合音` contraction, `又音`/`又唸作` also read. Notes stay with their reading in `PojUnicodeOthers`. When the first reading carries a note (`[[hio̍h]]（替）, [[ia̍p]]` for `葉`), it is repeated in `PojUnicodeOthers` with it — `PojUnicode` is `hio̍h`, `PojUnicodeOthers` is `hio̍h(替)/ia̍p` — since the note has no column of its own. Readings in templates carry their dialect codes as the note: `Ji̍t-pún(zz,kh)/Li̍t-pún(xm,qz,tp)`.
- **`HanLoTaibunPoj` of Pe̍h-ōe-jī pages.** From the `tas=` (漢), `tra=` (繁) or `orig=` (本) parameter of the page's nan-* templates, then from its `Hàn-jī` section; `sim=` (簡) is not Taigi writing and is not used. A page that is several words at once (`ka`: 家, 鳩, 鉸, 加) keeps one row, its Hanji, definitions and translations each joined.
- **Definitions, part of speech, translations.** Read from the page's Taigi section only: the lines of its part-of-speech and `Kái-soeh`/`意思` sections (examples, `#:` lines, left out), its part-of-speech headings and templates, and the `Eng-gú`, `Hôa-gú`, `Ji̍t-gí` lines of its translation table, with wiki markup and parenthesised romanisations dropped.
- **`LaigoanBangchi`.** `https://zh-min-nan.wiktionary.org/wiki/` + the page title with spaces as `_`, *not* percent-encoded, which is how the ChhoeTaigi database stores it; only `?` is written `%3F`.

## Caveats

### 1. Wiktionary is uneven

The 787 Pe̍h-ōe-jī pages were written by hand over many years in several layouts; the converter reads the layouts in use, and what it could not place is counted in the report (section headings not used, lines not read). The Hanji pages are regular, but their `意思` sections are mostly empty placeholders: only 2,211 have a definition.

### 2. Readings are published as written

27 readings are not in Pe̍h-ōe-jī spelling (KPL `oo-thinn-àm-tē`, `Tsheng-tāi`, `honn`); they are listed in the report and left as written, since the mirror is faithful to its source. A Hanji page with only another dialect's reading (泉州話, 漳州話…) gives no row (4 pages).

### 3. `HoaBun` is the first form only

A translation line usually lists the traditional and the simplified form (`[[螞蟻]], [[蚂蚁]] (mǎyǐ)`); only the first, `螞蟻`, is given. The mirror has no conversion table, so a page that lists the simplified form first gives that, and a line that lists two different words (`[[假使]], [[假如]]`) gives the first. `EngBun` and `JitBun` keep every form.

### 4. The page's own ASCII spelling can disagree with `PojInput`

150 Pe̍h-ōe-jī pages give their own tone-number spelling (`pojt=`); 4 disagree with `PojInput` (`chôa` is spelled `choa3` on the page). Both are kept as they are; the report lists them.

### 5. Differences from ChhoeTaigi's earlier import

ChhoeTaigi's 2024 import (1,481 rows, from the `all-titles-in-ns0` dump of 2024-10-20, titles only) compares as follows, matched on `LaigoanBangchi`:

| | rows |
|---|---|
| identical `PojUnicode` | 706 |
| corrected text (`o·` → `o͘`) | 10 |
| redirects — now not rows; the target is | 181 |
| Pe̍h-ōe-jī-looking title with no Taigi content (`ant`, `Antigua e Barbuda`) — dropped | 493 |
| index pages — dropped | 47 |
| no longer in the dump (Bân-tang-oē entries deleted since) | 44 |

15,796 rows are new to ChhoeTaigi: the 15,725 Hanji pages with a reading, and 71 Pe̍h-ōe-jī pages written since 2024.

## Chu-liāu bāng-chí

資料下載

1. [Wikimedia dumps for zh_min_nanwiktionary](https://dumps.wikimedia.org/zh_min_nanwiktionary/) — from each monthly run, `pages-articles.xml.bz2` (~3.6 MB), every current page with its wikitext.

The pipeline reads `latest/zh_min_nanwiktionary-latest-pages-articles.xml.bz2-rss.xml` to find the dated run that `latest` points at and downloads the dated file, so `manifest.json` records a URL that keeps resolving after `latest/` has moved on. If the RSS cannot be read, the run stops without publishing.

## Source

Original data source: Wiktionary (Wiki詞典) <https://zh-min-nan.wiktionary.org/>

## Terminology

- **Taigi** — the language. Written in Hanji and in Roman Orthography. The Wiktionary calls itself `Tâi-oân-ōe` (臺灣話), hence the repo name.
- **Pe̍h-ōe-jī (POJ)** — the Taigi Roman-script Orthography in the Presbyterian tradition. Columns `PojUnicode` and `PojInput`.
- **Hàn-jī** (漢字) — Taigi written in Chinese characters. Column `HanLoTaibunPoj` (漢羅台文).
- **bûn-jī** (文字) — text data. Directory `bunji/`.
- **táng-ló͘** (檔路) — download; a loan of English "download". Directory `tangloo/`, holding the dump as downloaded rather than anything this repo publishes. Never committed.
- **hun-lūi** (分類) — classification; here the part of speech. Column `Hunlui`.
- **kái-soeh** (解說) — explanation, definition. Columns `KaisoehPoj`, `KaisoehHanLoPoj`.
- **Eng-bûn, Hôa-bûn, Ji̍t-bûn** (英文, 華文, 日文) — English, Chinese, Japanese. Columns `EngBun`, `HoaBun`, `JitBun`.
- **lâi-goân bāng-chí** (來源網址) — source URL. Column `LaigoanBangchi`.
