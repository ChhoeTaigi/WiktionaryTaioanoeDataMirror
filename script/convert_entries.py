"""Build the ChhoeTaigi table of the Taigi entries in the Taigi Wiktionary.

Input is the `pages-articles.xml.bz2` dump of zh-min-nan.wiktionary.org (every
current page with its wikitext). Two kinds of main-namespace page are Taigi
entries:

- a page titled in Pe̍h-ōe-jī (`A-chiu`, `chhiú`), whose Hanji, part of
  speech, definitions and translations are written in its Taigi section;
- a page titled in Hanji (`亞洲`, `手`), nearly all imported from the Ministry
  of Education dictionary, whose Taigi reading stands on its `*臺灣話：` line.

Each becomes one row with the ChhoeTaigi database's column names
(`PojUnicode`, `PojInput`, `PojUnicodeOthers`, `PojInputOthers`,
`HanLoTaibunPoj`, `Hunlui`, `KaisoehPoj`, `KaisoehHanLoPoj`, `EngBun`,
`HoaBun`, `JitBun`, `LaigoanBangchi`), the names `SoanntengBunjiMuitheSekin`
rows carry in ChhoeTaigiPlusWebsite, so the table loads without renaming.
"""
import argparse
import bz2
import collections
import csv
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from poj_text import (HYPHENATION, TEXT_CORRECTIONS, _has_caron_on_bearer,
                          attested_hyphenations, collation_key, contains_poj, is_poj,
                          poj_unicode_to_input, title_text)
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent))
    from poj_text import (HYPHENATION, TEXT_CORRECTIONS, _has_caron_on_bearer,
                          attested_hyphenations, collation_key, contains_poj, is_poj,
                          poj_unicode_to_input, title_text)

WIKI_BASE_URL = "https://zh-min-nan.wiktionary.org/wiki/"
ARTICLE_NS = "0"

TABLE_NAME = "WiktionaryTaioanoe"
REPORT_NAME = "WiktionaryTaioanoeDataQuality"
# Columns of the ChhoeTaigi database, so the table loads without renaming.
# PojUnicodeOthers / PojInputOthers hold the further readings in the format
# KauiokPooSutian uses for the same Ministry of Education data: `chi̍t(替)`,
# several joined with `/`.
COLUMNS = ["PojUnicode", "PojInput", "PojUnicodeOthers", "PojInputOthers",
           "HanLoTaibunPoj", "Hunlui", "KaisoehPoj", "KaisoehHanLoPoj",
           "EngBun", "HoaBun", "JitBun", "LaigoanBangchi"]
OTHERS_SEPARATOR = "/"
LIST_SEPARATOR = "; "

# How many examples each report section lists.
REPORT_SAMPLE_SIZE = 50

# --- Wikitext ---------------------------------------------------------------

HAN = re.compile(r"[\u2e80-\u2fdf\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0003ffff]")
LETTER = re.compile(r"[^\W\d_]")
# Applied line by line: an unclosed <ref> swallows the rest of its line only.
REF = re.compile(r"<ref\b[^<>]*/>|<ref\b[^<>]*>.*?</ref>|<ref\b.*$", re.S)
# Innermost templates; stripped until none is left, so nesting goes too.
TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
LINK = re.compile(r"\[\[([^\[\]|]*)(?:\|([^\[\]]*))?\]\]")
EXTERNAL_LINK = re.compile(r"\[(?:https?|ftp)://[^\s\]]*(?:\s+([^\]]*))?\]")
HTML_TAG = re.compile(r"<[^<>]+>")
QUOTES = re.compile(r"'{2,}")
HEADING = re.compile(r"^(={2,6})\s*(.*?)\s*=+\s*$")
CATEGORY = re.compile(r"\[\[\s*(?:Category|Lūi-pia̍t|分類|分类)\s*:\s*([^\]|]+)", re.I)
# Links that are not words: files, categories, interwikis to other projects.
NON_WORD_LINK = re.compile(r"^\s*(?:File|Image|Media|Category|Lūi-pia̍t|分類|分类|w|wikipedia|s|q)\s*:",
                           re.I)
SPACES = re.compile(r"[ \t\u00a0\u3000]+")
PARENTHESIS = re.compile(r"[（(]([^（）()]*)[）)]")
# A page's own ASCII spelling (`pojt=`) writes ⁿ as N and o͘ as ou.
POJT_NASAL = re.compile(r"N(?=\d|-|$| )")
POJT_OU = re.compile(r"ou(?=h?\d?(?:-|$| ))")


def strip_markup(text):
    """One line of wikitext → its plain text: references, templates, tags and
    quote marks dropped, links replaced by their label (`[[a|b]]` → b,
    `[[a]]` → a), file, category and interwiki links removed."""
    text = REF.sub("", text)
    while True:
        text, n = TEMPLATE.subn("", text)
        if not n:
            break

    def link(m):
        target, label = m.group(1), m.group(2)
        if NON_WORD_LINK.match(target):
            return ""
        if label is not None:
            return label
        return target.split("#", 1)[0]

    text = LINK.sub(link, text)
    text = EXTERNAL_LINK.sub(lambda m: m.group(1) or "", text)
    text = HTML_TAG.sub("", text)
    text = QUOTES.sub("", text)
    text = text.replace("&nbsp;", " ")
    return SPACES.sub(" ", text).strip()


def sections(text):
    """[(level, heading, [lines])] in page order; level 0 is the text before
    the first heading. The heading is plain text."""
    out = [(0, "", [])]
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            out.append((len(m.group(1)), strip_markup(m.group(2)), []))
        else:
            out[-1][2].append(line)
    return out


# Headings written in Hanji alone, keyed like their Pe̍h-ōe-jī equivalents.
HAN_HEADINGS = {"意思": "isu", "翻譯": "hoanek", "翻译": "hoanek", "漢字": "hanji", "汉字": "hanji",
                "名詞": "bengsu", "動詞": "tongsu", "形容詞": "hengiongsu", "副詞": "husu",
                "連詞": "liansu", "介詞": "kaisu", "助詞": "chosu", "代名詞": "taibengsu",
                "感嘆詞": "kamthansu", "數詞": "sosu", "量詞": "liongsu", "解說": "kaisoeh",
                "音": "im", "例": "le", "例句": "leku", "相關": "siongkoan", "參考": "chhamkho",
                "參考資料": "chhamkholaigoan"}


def heading_key(heading):
    """`Bêng-sû 名詞`, `bêngsû`, `Hêng-iông Sû` → `bengsu`, `hengiongsu`:
    the heading without Hanji, parentheses, marks, case or punctuation. A
    heading written in Hanji alone (`意思`) is keyed through HAN_HEADINGS."""
    text = PARENTHESIS.sub("", heading).strip()
    if text and HAN.sub("", text).strip() == "":
        return HAN_HEADINGS.get(text, "")
    text = HAN.sub("", text).replace("ⁿ", "nn")
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text.casefold()
                   if ch.isalnum() and not unicodedata.combining(ch))


# --- Which pages are Taigi entries ------------------------------------------

# The language headings a Taigi entry is written under (`== Tâi-oân-ōe ==`,
# `== Bân-lâm-gí ==`, `==閩南語==`), matched loosely: spellings vary.
TAIGI_LANGUAGE = re.compile(r"Tâi-oân|Bân-lâm|Bān-lâm|Bâm-lâm|Hô-ló|Hō-ló|Hok-kiàn|Tâi-g[íú]|Tâi-bûn"
                            r"|閩南|闽南|臺灣|台灣|台语|台語", re.I)
# Any language heading: `Eng-gú`, `Hoat-gí`, `Kheh-oē`, `Hôa-gú:`, `英語`,
# `Hoa̍h-gí-giân` (translingual). A page whose only language headings are
# foreign is not a Taigi entry, however Taigi its title looks.
LANGUAGE_HEADING = re.compile(r"(?:-g[úíîi]r?|-[oō][eē]|-bûn|-giân|語|语|話|话|文|^Volapük)\s*:?$")
TAIGI_CATEGORY = re.compile(r"^(?:Bân-lâm-g[úí]|Tâi-oân-[oō][eē]|nan(?:-tw|-cn)?)(?::|$)", re.I)
# `{{nan-noun|p|pojt=…|tas=…}}` and its siblings mark a Taigi entry too.
NAN_TEMPLATE = re.compile(r"\{\{(nan-[a-z]+)\|([^{}]*)\}\}")
# Index and appendix pages that sit in the main namespace.
INDEX_TITLE = re.compile(r"^(?:Sek-ín|Hū-le̍k|Hù-lio̍k|Appendix|Pe̍h-ōe-jī Sek-ín)\b", re.I)

# Section headings whose lines are definitions: parts of speech, `Kái-soeh`
# (explanation), `意思` (meaning). Keyed by heading_key(); the value is the
# part of speech written to `Hunlui`, or None for a heading that is not one.
POS_HEADINGS = {
    "bengsu": "Bêng-sû", "tongsu": "Tōng-sû", "tangsu": "Tōng-sû",
    "hengiongsu": "Hêng-iông-sû", "hingiongsu": "Hêng-iông-sû", "husu": "Hù-sû",
    "liansu": "Liân-sû", "kaisu": "Kài-sû", "chosu": "Chō-sû", "taibengsu": "Tāi-bêng-sû",
    "kamthansu": "Kám-thàn-sû", "liongsu": "Liōng-sû", "soji": "Sò͘-jī", "sosu": "Sò͘-sû",
    "bengsukiamtongsu": "Bêng-sû kiam tōng-sû", "tongsukiambengsu": "Tōng-sû kiam bêng-sû",
    "choaniumiasu": "Choan-iú miâ-sû", "cardinalnumber": "Sò͘-jī",
}
DEFINITION_HEADINGS = set(POS_HEADINGS) | {"kaisoeh", "kaisoe", "isu", "su"}
TRANSLATION_HEADINGS = {"hoanek", "translations", "hoanekhoanek"}
HANJI_HEADINGS = {"hanji", "tuitangehanji", "hanjihanji"}
# Template name → part of speech.
TEMPLATE_POS = {"nan-noun": "Bêng-sû", "nan-verb": "Tōng-sû", "nan-adjective": "Hêng-iông-sû",
                "nan-adverb": "Hù-sû", "nan-conjunction": "Liân-sû", "nan-particle": "Chō-sû",
                "nan-pronoun": "Tāi-bêng-sû"}
# Template parameters that give the entry's Hanji, in order of preference:
# 漢 (Taigi Hanji), 繁 (traditional), 本 (etymological). 簡 is not Taigi writing.
HANJI_PARAMS = ("tas", "tra", "orig")

# `*臺灣話：[[chúi]]` on a Hanji page; `*漳州話：…` for the count of pages
# that give only another dialect's reading.
READING_LINE = re.compile(r"^\*+\s*臺灣話\s*[:：](.*)$")
OTHER_DIALECT_LINE = re.compile(r"^\*+\s*(?:泉州話|廈門話|漳州話|潮州話|海南話|雷州話|同安話)\s*[:：]\s*\S")
READING_SEPARATORS = re.compile(r"[,，、/／;；]")
# "又唸作" (also read) introduces further readings; it is kept as their note.
ALSO_READ = "又唸作"
# A parenthesis holding only links is a reading too (`lo̍h--khì([[loeh]])`),
# not a note.
LINKED_PARENTHESIS = re.compile(r"[（(]((?:\s*\[\[[^\[\]]*\]\]\s*[,，、/／;；]?)+\s*)[）)]")
READING_TOKENS = re.compile(r"([,，、/／;；]|" + ALSO_READ + ")")
STASHED = re.compile("\x00(\\d+)\x00")
# `{{zh-pron|mn=tân/tîn}}`: readings in the English Wiktionary's template,
# each optionally prefixed by dialect codes (`zz,kh:Ji̍t-pún`).
ZH_PRON_MN = re.compile(r"\|\s*mn\s*=\s*([^|{}]*)")
# `* Bân-lâm-gí: [[Chng]]` in the translation table of a Mandarin entry
# (`莊`): the Taigi reading of the Hanji, used when the page gives no other.
# Only for a Hanji title: on a Malay or English page (`gua`) the same line
# is a translation, not a reading.
TAIGI_TRANSLATION_LINE = re.compile(r"^\*+\s*\[?\[?(?:Bân-lâm-g[íú]|Tâi-oân-[oō][eē]|Hō-ló-oē|Hô-ló-oē)"
                                    r"\]?\]?\s*[:：](.*)$")

TRANSLATION_LABELS = {
    "EngBun": re.compile(r"^(?:Eng-g[úíî]|Eng-bûn|English|英語|英文)$"),
    "HoaBun": re.compile(r"^(?:Hôa-g[úíî]|Hôa-bûn|Tiong-bûn|Tiong-kok-g[úí]|Mandarin|Chinese"
                         r"|華語|華文|华语|漢語|汉语|中文|國語)$"),
    "JitBun": re.compile(r"^(?:Ji̍t-g[úíî]|Ji̍t-bûn|Ji̍t-pún-ōe|Japanese|日語|日文|日本語)$"),
}
TRANSLATION_LINE = re.compile(r"^\*+\s*(.+?)\s*[:：]\s*(.*)$")
# Lines in a definition section that are not definitions: tables, files,
# categories, templates standing alone.
NOT_A_DEFINITION = ("{{", "}}", "{|", "|", "!", "<", "[[File:", "[[Image:", "[[Category:", "__")
LIST_MARKER = re.compile(r"^[#*:;]+\s*")
NUMBERING = re.compile(r"^(?:\(\d+\)|\d+[.)])\s*")
EXAMPLE_LINE = re.compile(r"^[#*]+[:*]")


def title_to_url(title):
    """Unencoded, as the ChhoeTaigi database stores `LaigoanBangchi`, with
    spaces as `_`; only `?` is encoded, which a browser would take as the
    start of the query string."""
    return WIKI_BASE_URL + title.replace(" ", "_").replace("?", "%3F")


def page_kind(title, redirect, text, readings):
    """How a page is treated: `redirect`, `index` (an index or appendix page),
    `poj` (a Pe̍h-ōe-jī title with Taigi content), `reading` (a page whose
    `*臺灣話：` line or nan-pron template gives a Taigi reading),
    `poj_not_taigi` (a Pe̍h-ōe-jī-looking title with no Taigi content: letters,
    foreign words), `hanji_no_reading`, or `other` (foreign-language entries)."""
    if redirect is not None:
        return "redirect"
    if INDEX_TITLE.match(title) or "://" in title:
        return "index"
    # Tested with spaces as `_`, as the all-titles dump writes them and the
    # 2024 import read them: a space-separated word then counts on its own.
    if contains_poj(title.replace(" ", "_")):
        if readings or taigi_content(text):
            return "poj"
        return "poj_not_taigi"
    if readings:
        return "reading"
    if HAN.search(title):
        return "hanji_no_reading"
    return "other"


def taigi_content(text):
    """True when the page has a Taigi section, a Taigi category or a nan-*
    template. A level-2 heading that names a part of speech or a translation
    table counts as a Taigi section: the wiki's own language is Taigi, so an
    entry structured without a language heading is a Taigi one."""
    for level, heading, _ in sections(text):
        if level == 2 and (TAIGI_LANGUAGE.search(heading)
                           or heading_key(heading) in DEFINITION_HEADINGS | TRANSLATION_HEADINGS):
            return True
    if NAN_TEMPLATE.search(text):
        return True
    return any(TAIGI_CATEGORY.match(c.strip()) for c in CATEGORY.findall(text))


def taigi_sections(secs):
    """The sections of a page that belong to its Taigi entry: those under a
    Taigi language heading; or, on a page with no language heading at all,
    every section; or, beside foreign-language headings, the preamble and the
    level-2 sections that name no language."""
    language = {i for i, (level, heading, _) in enumerate(secs)
                if level == 2 and (TAIGI_LANGUAGE.search(heading) or LANGUAGE_HEADING.search(heading))}
    taigi = {i for i in language if TAIGI_LANGUAGE.search(secs[i][1])}
    if not language:
        return secs
    chosen = []
    keep = not taigi  # the preamble, when no section is a Taigi language one
    for i, sec in enumerate(secs):
        if sec[0] == 2:
            keep = i in taigi if taigi else i not in language
        if keep:
            chosen.append(sec)
    return chosen


# --- Readings ---------------------------------------------------------------

def parse_reading_line(line):
    """`[[jîn]]/[[lîn]], [[lâng]]（替）` → ([(reading, note)], leftover text that
    could not be read as a reading). Readings are separated by `,`, `、`, `/`
    or `;`; a parenthesis after a reading annotates it (文 literary, 替
    substitute character, 俗 popular…); "又唸作" annotates what follows."""
    text = REF.sub("", line)
    while True:
        text, n = TEMPLATE.subn("", text)
        if not n:
            break
    text = LINKED_PARENTHESIS.sub(lambda m: ", " + strip_markup(m.group(1)), text)
    text = strip_markup(text)
    # Each parenthesis is set aside whole, innermost first, so a separator
    # or "又唸作" inside one never splits the line.
    stashed = []

    def stash(m):
        stashed.append(m.group(1))
        return f"\x00{len(stashed) - 1}\x00"

    def restore(note):
        return STASHED.sub(lambda m: "(" + restore(stashed[int(m.group(1))]) + ")", note)

    while True:
        text, n = PARENTHESIS.subn(stash, text)
        if not n:
            break
    readings, leftovers = [], []
    note = ""
    for piece in READING_TOKENS.split(text):
        if piece == ALSO_READ:
            note = ALSO_READ
            continue
        if READING_SEPARATORS.fullmatch(piece):
            continue
        notes = [restore(stashed[int(i)]).strip(" 〔〕[]") for i in STASHED.findall(piece)]
        notes = [n for n in notes if n]
        reading = SPACES.sub(" ", STASHED.sub(" ", piece)).strip(" .;:[]")
        if not reading:
            if notes and readings:
                readings[-1] = (readings[-1][0], "、".join(filter(None, [readings[-1][1]] + notes)))
            continue
        if HAN.search(reading) or not LETTER.search(reading):
            leftovers.append(reading)
            continue
        readings.append((reading, "、".join(filter(None, [note] + notes))))
    return readings, leftovers


def template_params(body):
    """`p|pojt=chhiu2|tas=手` → (["p"], {"pojt": "chhiu2", "tas": "手"})."""
    positional, named = [], {}
    for part in body.split("|"):
        if "=" in part:
            key, value = part.split("=", 1)
            named[key.strip()] = value.strip()
        else:
            positional.append(part.strip())
    return positional, named


def page_readings(title, text):
    """The page's readings: [(reading, note)] from its `*臺灣話：` lines — or,
    when it has none, its nan-pron templates (note: their `loc`) — plus the
    `poj` and `vary` parameters of its nan-* templates. Also the lines whose
    text could not all be read, as (line, leftovers), whether another
    dialect's line has a reading, and whether the readings came from
    nan-pron templates."""
    readings, unparsed = [], []
    for line in text.splitlines():
        m = READING_LINE.match(line)
        if m:
            found, leftovers = parse_reading_line(m.group(1))
            readings += found
            if leftovers:
                unparsed.append((strip_markup(m.group(1)), leftovers))
    if not readings:
        # The English Wiktionary's pronunciation template: `mn=tân/tîn`,
        # `mn=zz,kh:Ji̍t-pún/xm,qz,tp:Li̍t-pún` (dialect codes kept as the note).
        for value in ZH_PRON_MN.findall(text):
            for part in strip_markup(value).split("/"):
                codes, _, reading = part.strip().rpartition(":")
                if reading and LETTER.search(reading) and not HAN.search(reading):
                    readings.append((reading, codes.strip()))
    if not readings and HAN.search(title):
        for line in text.splitlines():
            m = TAIGI_TRANSLATION_LINE.match(line)
            if m:
                found, leftovers = parse_reading_line(m.group(1))
                readings += found
    from_nan_pron = False
    if not readings:
        for name, body in NAN_TEMPLATE.findall(text):
            if name == "nan-pron":
                positional, named = template_params(body)
                reading = strip_markup(positional[0]) if positional else ""
                if reading and LETTER.search(reading) and not HAN.search(reading):
                    readings.append((reading, named.get("loc", "")))
                    from_nan_pron = True
    for name, body in NAN_TEMPLATE.findall(text):
        _, named = template_params(body)
        for key in ("poj", "vary"):
            for value in READING_SEPARATORS.split(strip_markup(named.get(key, ""))):
                value = value.strip()
                if value and LETTER.search(value) and not HAN.search(value):
                    readings.append((value, ""))
    other_dialect = any(OTHER_DIALECT_LINE.match(line) for line in text.splitlines())
    return {"readings": readings, "unparsed": unparsed, "other_dialect": other_dialect,
            "from_nan_pron": from_nan_pron}


# --- Hanji, part of speech, definitions, translations -----------------------

def _hanji_from_line(line):
    """Hanji forms on one line of a Hàn-jī section: `[[毋]][[通]]` and
    `[[假]]+[[使]]` are one form each, `[[根原]], [[根源]]` are two, and a link
    labelled `*` names the whole word (`[[題]][[目]] [[題目|*]]`)."""
    whole = [t for t, label in LINK.findall(line) if label == "*"]
    if whole:
        return [whole[0].strip()]
    out = []
    # `* Chiàⁿ-jī: …` / `* Sio̍k-jī: …`: a label holding no link or Hanji is
    # dropped; `[[毋]][[通]]: chù` keeps its Hanji.
    m = re.match(r"^(\*+\s*)([^:：\[\]]*)[:：]\s*", line.strip())
    body = line.strip()
    if m and not HAN.search(m.group(2)):
        body = body[m.end():]
    for piece in READING_SEPARATORS.split(body):
        targets = [t.split("#", 1)[0] for t, _ in LINK.findall(piece) if not NON_WORD_LINK.match(t)]
        form = "".join(targets) if targets else PARENTHESIS.sub("", strip_markup(piece))
        form = re.sub(r"[\s+?.]", "", form)
        if form and HAN.search(form):
            out.append(form)
    return out


def _clean_definition(line, title):
    """One definition line → plain text, or None when the line is not one:
    an example (`#:`), a table or file line, the bold headword, or empty."""
    stripped = line.strip()
    if not stripped or stripped.startswith(NOT_A_DEFINITION) or EXAMPLE_LINE.match(stripped):
        return None
    text = strip_markup(NUMBERING.sub("", LIST_MARKER.sub("", stripped)))
    text = NUMBERING.sub("", text).strip()
    if not text or not (LETTER.search(text) or HAN.search(text)):
        return None
    if text.casefold() == title.casefold():
        return None
    return text


def _clean_translation(value, column):
    """`[[螞蟻]], [[蚂蚁]] (mǎyǐ)` → `螞蟻`: markup dropped and, for Chinese
    and Japanese, the parenthesised readings too; Chinese keeps only the
    first form listed. English keeps its parentheses, which carry glosses
    (`admit (into membership)`)."""
    text = strip_markup(value)
    if column != "EngBun":
        while True:
            text, n = PARENTHESIS.subn("", text)
            if not n:
                break
    text = re.sub(r"\s+([,;，、])", r"\1", text)
    text = re.sub(r"([,;，、])(?:\s*[,;，、])+", r"\1", text)
    text = SPACES.sub(" ", text).strip(" ,;，、:：.")
    if column == "HoaBun":
        # Only the first form a line lists: a page that gives the
        # traditional and the simplified form gives the traditional.
        text = re.split(r"\s*[,;，、/]\s*", text, 1)[0]
    return text


def page_entry(title, text):
    """What the Taigi section of a page says about the word: its Hanji (in
    order found; from nan-* templates first, then Hàn-jī sections), parts of
    speech, definitions, translations, the page's own ASCII spelling
    (`pojt`), and the headings of its Taigi section that were not used."""
    hanji, pos, definitions, pojt = [], [], [], []
    translations = {column: [] for column in TRANSLATION_LABELS}
    skipped = collections.Counter()
    for name, body in NAN_TEMPLATE.findall(text):
        positional, named = template_params(body)
        for key in HANJI_PARAMS:
            form = strip_markup(named.get(key, "")).split(OTHERS_SEPARATOR, 1)[0].strip()
            if form and HAN.search(form):
                hanji.append(form)
        if name in TEMPLATE_POS and positional and positional[0] == "p":
            pos.append(TEMPLATE_POS[name])
        if named.get("pojt"):
            pojt.append(named["pojt"])
    for level, heading, lines in taigi_sections(sections(text)):
        key = heading_key(heading)
        if key in DEFINITION_HEADINGS:
            if POS_HEADINGS.get(key):
                pos.append(POS_HEADINGS[key])
            for line in lines:
                cleaned = _clean_definition(line, title)
                if cleaned:
                    definitions.append(cleaned)
        elif key in HANJI_HEADINGS:
            for line in lines:
                if line.strip().startswith(("*", "[[", ":")) and not CATEGORY.search(line):
                    hanji += _hanji_from_line(line)
        elif key in TRANSLATION_HEADINGS or level == 0:
            for line in lines:
                m = TRANSLATION_LINE.match(line)
                if not m:
                    continue
                label = strip_markup(m.group(1))
                for column, pattern in TRANSLATION_LABELS.items():
                    if pattern.match(label):
                        value = _clean_translation(m.group(2), column)
                        if value:
                            translations[column].append(value)
        elif heading and not (level == 2 and (TAIGI_LANGUAGE.search(heading)
                                              or LANGUAGE_HEADING.search(heading))):
            skipped[heading] += 1
    for name, body in [m.groups() for m in re.finditer(r"\{\{(zh-forms)\|([^{}]*)\}\}", text)]:
        positional, _ = template_params(body)
        form = strip_markup(positional[1]) if len(positional) > 1 else ""
        if form and HAN.search(form):
            hanji.append(re.sub(r"\s+", "", form))
    return {
        "hanji": list(dict.fromkeys(hanji)),
        "pos": list(dict.fromkeys(pos)),
        "definitions": list(dict.fromkeys(definitions)),
        "translations": {c: list(dict.fromkeys(v)) for c, v in translations.items()},
        "pojt": pojt,
        "skipped_headings": skipped,
    }


def pojt_matches(pojt, poj_input):
    """Whether the page's own ASCII spelling (`pojt=chhiu2`, with ⁿ as N and
    o͘ as ou) agrees with PojInput. Only the first of several is compared."""
    given = pojt.split(",", 1)[0].strip()
    given = POJT_OU.sub("oo", POJT_NASAL.sub("nn", given))
    return given.casefold() == poj_input.casefold()


# --- I/O --------------------------------------------------------------------

def _child_text(el, name):
    for child in el:
        if child.tag.rsplit("}", 1)[-1] == name:
            return child
    return None


def read_pages(dump_path):
    """Yields (title, redirect target or None, wikitext) for every page of
    the main namespace, in dump order. Reads .xml.bz2 or plain .xml."""
    opener = bz2.open if str(dump_path).endswith(".bz2") else open
    with opener(dump_path, "rb") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag.rsplit("}", 1)[-1] != "page":
                continue
            ns = _child_text(el, "ns")
            if ns is not None and (ns.text or "").strip() == ARTICLE_NS:
                title = (_child_text(el, "title").text or "").strip()
                redirect = _child_text(el, "redirect")
                revision = _child_text(el, "revision")
                text_el = _child_text(revision, "text") if revision is not None else None
                text = (text_el.text if text_el is not None else None) or ""
                if title:
                    yield title, (redirect.get("title") if redirect is not None else None), text
            el.clear()


def write_csv(rows, columns, path):
    # utf-8-sig (BOM) so Excel auto-detects UTF-8 — the sibling mirrors'
    # convention — every field quoted, always with a header row.
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def write_json(payload, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_json_rows(rows, path):
    """A JSON array with one compact record per line, as the Wikipedia mirror
    writes its table: it diffs line by line."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("[\n")
        for i, row in enumerate(rows):
            f.write(json.dumps(row, ensure_ascii=False))
            f.write(",\n" if i < len(rows) - 1 else "\n")
        f.write("]\n")


# --- Report -----------------------------------------------------------------

def _shown(total, shown, noun):
    text = f"{total:,} {noun}{'' if total == 1 else 's'}"
    return text + (f"; the first {shown} are shown." if shown < total else ".")


def _md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        cells = [str(c).replace("|", "\\|").replace("\n", " ") for c in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _code(text):
    return "`" + str(text).replace("`", "'") + "`"


def _sample(items, render, noun):
    shown = items[:REPORT_SAMPLE_SIZE]
    return [render(shown), "", _shown(len(items), len(shown), noun), ""]


def render_report_md(report, source_name):
    c = report["counts"]
    parts = [
        f"# {REPORT_NAME}",
        "",
        f"Source dump: `{source_name}`",
        "",
        "## Counts",
        "",
        _md_table(["", "count"], [
            ["Main-namespace pages in dump", f"{c['pages_total']:,}"],
            ["Rows published", f"{c['rows']:,}"],
            ["… from a Pe̍h-ōe-jī title", f"{c['rows_poj_title']:,}"],
            ["… from a Hanji (or other) title with a 臺灣話 reading", f"{c['rows_reading_title']:,}"],
            ["… with `HanLoTaibunPoj`", f"{c['rows_HanLoTaibunPoj']:,}"],
            ["… with further readings (`PojUnicodeOthers`)", f"{c['rows_PojUnicodeOthers']:,}"],
            ["… with a definition (`KaisoehPoj` or `KaisoehHanLoPoj`)",
             f"{c['rows_KaisoehPoj'] + c['rows_KaisoehHanLoPoj']:,}"],
            ["… with `EngBun`, `HoaBun` or `JitBun`", f"{c['rows_translated']:,}"],
            ["… whose text was corrected", f"{c['rows_text_corrected']:,}"],
            ["… with a multi-tone word", f"{c['rows_multi_tone']:,}"],
            ["… with a caron on a tone-bearing letter", f"{c['rows_caron']:,}"],
        ]),
        "",
        "## 1. Pages — which became rows",
        "",
        "A page is a Taigi entry when its title is Pe̍h-ōe-jī and it has Taigi",
        "content (a Taigi language heading, a Taigi category, a nan-* template or",
        "a `*臺灣話：` reading), or when its `*臺灣話：` line gives a reading, whatever",
        "the title. Redirects are not rows: their target is. Every other page is",
        "dropped and counted here.",
        "",
        _md_table(["pages", "count"], [
            ["Rows: Pe̍h-ōe-jī title with Taigi content", f"{c['rows_poj_title']:,}"],
            ["… of which the page also has a `*臺灣話：` reading", f"{c['rows_poj_title_with_reading']:,}"],
            ["Rows: title with a 臺灣話 reading", f"{c['rows_reading_title']:,}"],
            ["… of which the title is not Hanji", f"{c['rows_reading_title_not_hanji']:,}"],
            ["Dropped: redirects", f"{c['pages_redirect']:,}"],
            ["Dropped: Pe̍h-ōe-jī-looking title, no Taigi content (listed below)",
             f"{c['pages_poj_not_taigi']:,}"],
            ["Dropped: Hanji title without a 臺灣話 reading", f"{c['pages_hanji_no_reading']:,}"],
            ["… of which another dialect's line has a reading", f"{c['pages_other_dialect_only']:,}"],
            ["Dropped: index and appendix pages", f"{c['pages_index']:,}"],
            ["Dropped: entries of other languages", f"{c['pages_other']:,}"],
        ]),
        "",
        "### Pe̍h-ōe-jī-looking titles with no Taigi content — dropped",
        "",
        "Single letters, index pages and words of other languages whose title",
        "happens to parse as Pe̍h-ōe-jī syllables (`ant`, `sin`, `net`).",
        "",
    ]
    parts += _sample(report["poj_not_taigi"], lambda s: ", ".join(_code(t) for t in s), "title")
    parts += [
        "### Hanji titles without a 臺灣話 reading — dropped",
        "",
    ]
    parts += _sample(report["hanji_no_reading"], lambda s: ", ".join(_code(t) for t in s), "title")
    parts += [
        "### Index and appendix pages — dropped",
        "",
    ]
    parts += _sample(report["index_pages"], lambda s: ", ".join(_code(t) for t in s), "title")
    parts += [
        "## 2. Text — corrections",
        "",
        "`PojUnicode` and the readings are made as good as possible for finding by",
        "Pe̍h-ōe-jī; `LaigoanBangchi` keeps the exact page. These corrections were",
        "made (a row counts once per correction, whichever column it was in):",
        "",
        _md_table(["correction", "rows"], [[name, f"{n:,}"] for name, n in report["corrections"] if n]),
        "",
        "Run-together syllables are split only into a hyphenated form that the",
        "wiki's own titles and readings use somewhere, so a foreign name that",
        "happens to parse as syllables is never split.",
        "",
    ]
    splits = report.get("hyphenated_words") or []
    if splits:
        parts += [
            _md_table(["written", "corrected", "rows"],
                      [[_code(w), _code(sp), n] for w, sp, n in splits[:REPORT_SAMPLE_SIZE]]),
            "",
            _shown(len(splits), min(REPORT_SAMPLE_SIZE, len(splits)), "distinct word"),
            "",
        ]
    corrected = report["corrected_rows"]
    if corrected:
        parts += [
            _md_table(["page", "written", "corrected", "corrections"],
                      [[_code(r["title"]), _code(r["written"]), _code(r["corrected"]),
                        ", ".join(r["corrections"])] for r in corrected[:REPORT_SAMPLE_SIZE]]),
            "",
            _shown(len(corrected), min(REPORT_SAMPLE_SIZE, len(corrected)), "corrected value")
            + f" All are in `{REPORT_NAME}.json`.",
            "",
        ]
    parts += [
        "## 3. Readings — `PojUnicode` and `PojUnicodeOthers` of Hanji pages",
        "",
        "The `*臺灣話：` line of a Hanji page gives one reading or several",
        "(`[[jîn]]/[[lîn]], [[lâng]]（替）`), some annotated: 文 literary reading,",
        "替 the Hanji is a substitute character for this reading, 俗/俗音 popular",
        "pronunciation, 合音 contraction, 又音/又唸作 also read. The first reading",
        "is `PojUnicode`; the rest are `PojUnicodeOthers`, each with its note in",
        "parentheses, joined with `/` — the format KauiokPooSutian uses for the",
        "same Ministry of Education data. A first reading that carries a note is",
        "repeated in `PojUnicodeOthers` with it, since the note has no column of",
        "its own.",
        "",
        _md_table(["", "count"], [
            ["Readings published", f"{c['readings']:,}"],
            ["… with a note", f"{c['readings_annotated']:,}"],
            ["First readings with a note (repeated in `PojUnicodeOthers`)",
             f"{c['readings_first_annotated']:,}"],
            ["Readings taken from a nan-pron template (no 臺灣話 line)", f"{c['readings_from_nan_pron']:,}"],
            ["Readings not in Pe̍h-ōe-jī spelling (listed below)", f"{c['readings_not_poj']:,}"],
            ["Reading lines with text that could not be read (listed below)",
             f"{c['reading_lines_unparsed']:,}"],
        ]),
        "",
        _md_table(["note", "readings"], [[_code(n), f"{k:,}"] for n, k in report["reading_notes"]]),
        "",
        "### Readings not in Pe̍h-ōe-jī spelling — published as written",
        "",
        "KPL spellings (`oo`, `nn`, `ts`), tone numbers or other slips; the",
        "mirror is faithful and does not correct them.",
        "",
    ]
    parts += _sample(report["readings_not_poj"],
                     lambda s: _md_table(["page", "reading"], [[_code(t), _code(r)] for t, r in s]),
                     "reading")
    parts += [
        "### Reading lines with text that could not be read",
        "",
    ]
    parts += _sample(report["reading_lines_unparsed"],
                     lambda s: _md_table(["page", "line", "not read"],
                                         [[_code(t), _code(l), ", ".join(_code(x) for x in left)]
                                          for t, l, left in s]),
                     "line")
    parts += [
        "## 4. Hanji of Pe̍h-ōe-jī pages — `HanLoTaibunPoj`",
        "",
        "From the `tas=` (漢), `tra=` (繁) or `orig=` (本) parameter of the page's",
        "nan-* templates, then from its `Hàn-jī` section. Several forms are",
        "joined with `/`.",
        "",
        _md_table(["", "count"], [
            ["Pe̍h-ōe-jī pages with Hanji", f"{c['rows_poj_title_with_hanji']:,}"],
            ["… with more than one form (listed below)", f"{c['rows_hanji_multiple']:,}"],
            ["Pe̍h-ōe-jī pages without Hanji", f"{c['rows_poj_title'] - c['rows_poj_title_with_hanji']:,}"],
        ]),
        "",
    ]
    parts += _sample(report["hanji_multiple"],
                     lambda s: _md_table(["page", "`HanLoTaibunPoj`"], [[_code(t), _code(h)] for t, h in s]),
                     "page")
    parts += [
        "## 5. Multi-tone words — `PojInput` left unconverted",
        "",
        "A Pe̍h-ōe-jī syllable carries at most one tone mark. A word with two or",
        "more that could not be split into syllables is copied into `PojInput`",
        "as written rather than guessed at.",
        "",
    ]
    total = len(report["multi_tone_words_all"])
    if total:
        parts += [
            _md_table(["word", "rows"], [[_code(w), n] for w, n in report["multi_tone_words"]]),
            "",
            (f"{total:,} distinct multi-tone words; the {len(report['multi_tone_words'])} "
             f"most frequent are shown. The full list is in `{REPORT_NAME}.json`."
             if len(report["multi_tone_words"]) < total
             else _shown(total, total, "distinct multi-tone word")),
            "",
        ]
    caron = report.get("caron_rows") or []
    if caron:
        parts += [
            "### Caron on a tone-bearing letter — left as written",
            "",
            "A caron (`ǔ`, `ě`) is not read as a tone mark, as in KonvertToPOJ.",
            "",
            ", ".join(_code(t) for t in caron[:REPORT_SAMPLE_SIZE]),
            "",
            _shown(len(caron), min(REPORT_SAMPLE_SIZE, len(caron)), "row"),
            "",
        ]
    parts += [
        "## 6. The page's own ASCII spelling — `pojt=` against `PojInput`",
        "",
        "Pe̍h-ōe-jī pages with a nan-* template give their own tone-number",
        "spelling (`pojt=chhiu2`, writing ⁿ as `N` and o͘ as `ou`). Where it",
        "disagrees with `PojInput`, one of the two is wrong on the page; nothing",
        "is changed here.",
        "",
        _md_table(["", "count"], [
            ["Pages with a `pojt=`", f"{c['pojt_pages']:,}"],
            ["… agreeing with `PojInput`", f"{c['pojt_pages'] - c['pojt_mismatch']:,}"],
            ["… differing (listed below)", f"{c['pojt_mismatch']:,}"],
        ]),
        "",
    ]
    parts += _sample(report["pojt_mismatch"],
                     lambda s: _md_table(["page", "`pojt=`", "`PojInput`"],
                                         [[_code(t), _code(g), _code(p)] for t, g, p in s]),
                     "page")
    parts += [
        "## 7. Definitions, parts of speech and translations",
        "",
        "From the Taigi section of each page: the lines of its part-of-speech",
        "and `Kái-soeh`/`意思` sections are `KaisoehPoj` (Pe̍h-ōe-jī pages) or",
        "`KaisoehHanLoPoj` (Hanji pages), one per line, examples left out; the",
        "part-of-speech headings and templates give `Hunlui`; the `Eng-gú`,",
        "`Hôa-gú` and `Ji̍t-gí` lines of its translation table give `EngBun`,",
        "`HoaBun` and `JitBun`, markup and romanisations dropped.",
        "",
        _md_table(["column", "rows"], [
            ["`Hunlui`", f"{c['rows_Hunlui']:,}"],
            ["`KaisoehPoj`", f"{c['rows_KaisoehPoj']:,}"],
            ["`KaisoehHanLoPoj`", f"{c['rows_KaisoehHanLoPoj']:,}"],
            ["`EngBun`", f"{c['rows_EngBun']:,}"],
            ["`HoaBun`", f"{c['rows_HoaBun']:,}"],
            ["`JitBun`", f"{c['rows_JitBun']:,}"],
        ]),
        "",
        "### Section headings in Taigi entries that were not used",
        "",
        "Sections other than definitions, Hanji and translations are not read",
        "(examples, proverbs, references, KPL spelling…). The most frequent:",
        "",
        _md_table(["heading", "pages"], [[_code(h), f"{n:,}"] for h, n in report["skipped_headings"]]),
        "",
        f"Full lists are in `{REPORT_NAME}.json`.",
        "",
    ]
    return "\n".join(parts)


# --- Entry point ------------------------------------------------------------

def _others(readings):
    """`PojUnicodeOthers` and `PojInputOthers` for readings, each with its
    note in parentheses, joined with `/`; and the multi-tone words met."""
    unicode_parts, input_parts, multi = [], [], []
    for reading, note in readings:
        converted, multi_words = poj_unicode_to_input(reading)
        multi += multi_words
        suffix = f"({note})" if note else ""
        unicode_parts.append(reading + suffix)
        input_parts.append(converted + suffix)
    return OTHERS_SEPARATOR.join(unicode_parts), OTHERS_SEPARATOR.join(input_parts), multi


def convert_entries(dump_path, bunji_dir, report_dir=None):
    """Builds bunji/WiktionaryTaioanoe.{csv,json} and the report. Returns counts."""
    dump_path = Path(dump_path)
    bunji_dir = Path(bunji_dir)
    report_dir = Path(report_dir) if report_dir else bunji_dir.parent
    bunji_dir.mkdir(parents=True, exist_ok=True)

    pages = list(read_pages(dump_path))
    # Hyphenated forms are attested by every title and every reading.
    parsed = {title: page_readings(title, text) for title, redirect, text in pages if redirect is None}
    attested = attested_hyphenations([t for t, _, _ in pages]
                                     + [r for p in parsed.values() for r, _ in p["readings"]])

    counts = collections.Counter()
    lists = collections.defaultdict(list)
    correction_counts = collections.Counter()
    split_counter = collections.Counter()
    multi_counter = collections.Counter()
    note_counter = collections.Counter()
    skipped_headings = collections.Counter()
    entries = []

    def correct(value, title, column):
        """value with the text corrections applied, listed when any was made."""
        fixed, made, splits = title_text(value, attested)
        if made:
            correction_counts.update(made)
            split_counter.update(set(splits))
            lists["corrected_rows"].append({"title": title, "column": column, "written": value,
                                            "corrected": fixed, "corrections": made})
        return fixed, bool(made)

    for title, redirect, text in pages:
        counts["pages_total"] += 1
        page = parsed.get(title) or {"readings": [], "unparsed": [], "other_dialect": False,
                                     "from_nan_pron": False}
        readings = page["readings"]
        kind = page_kind(title, redirect, text, readings)
        counts[f"pages_{kind}"] += 1
        if kind == "redirect":
            lists["redirects"].append([title, redirect])
            continue
        if kind == "index":
            lists["index_pages"].append(title)
            continue
        if kind == "poj_not_taigi":
            lists["poj_not_taigi"].append(title)
            continue
        if kind == "hanji_no_reading":
            lists["hanji_no_reading"].append(title)
            if page["other_dialect"]:
                counts["pages_other_dialect_only"] += 1
            continue
        if kind == "other":
            continue

        # One row. Readings are corrected like titles and deduplicated; a
        # reading equal to the Pe̍h-ōe-jī title is the title, not another.
        for line, leftovers in page["unparsed"]:
            lists["reading_lines_unparsed"].append([title, line, leftovers])
        corrected_any = False
        seen, kept = set(), []
        for reading, note in readings:
            reading, made = correct(reading, title, "reading")
            corrected_any |= made
            if reading in seen:
                continue
            seen.add(reading)
            kept.append((reading, note))
            if not is_poj(reading):
                lists["readings_not_poj"].append([title, reading])
        readings = kept
        entry = page_entry(title, text)
        skipped_headings.update(entry["skipped_headings"])
        row = dict.fromkeys(COLUMNS, "")
        multi = []
        if kind == "poj":
            poj, made = correct(title, title, "PojUnicode")
            corrected_any |= made
            # A reading equal to the title is the title; every other one is
            # a further reading.
            others = [(r, n) for r, n in readings if r != poj]
            row["HanLoTaibunPoj"] = OTHERS_SEPARATOR.join(entry["hanji"])
            row["Hunlui"] = OTHERS_SEPARATOR.join(entry["pos"])
            row["KaisoehPoj"] = "\n".join(entry["definitions"])
            if page["readings"]:
                counts["rows_poj_title_with_reading"] += 1
            if entry["hanji"]:
                counts["rows_poj_title_with_hanji"] += 1
                if len(entry["hanji"]) > 1:
                    counts["rows_hanji_multiple"] += 1
                    lists["hanji_multiple"].append([title, row["HanLoTaibunPoj"]])
        else:
            poj, note = readings[0]
            # The first reading's note has no column of its own: the reading
            # is repeated with it among the others.
            others = ([readings[0]] if note else []) + readings[1:]
            counts["readings_first_annotated"] += bool(note)
            row["HanLoTaibunPoj"] = title
            row["KaisoehHanLoPoj"] = "\n".join(entry["definitions"])
            if not HAN.search(title):
                counts["rows_reading_title_not_hanji"] += 1
            if page["from_nan_pron"]:
                counts["readings_from_nan_pron"] += len(readings)
        row["PojUnicode"] = poj
        row["PojInput"], multi_words = poj_unicode_to_input(poj)
        multi += multi_words
        row["PojUnicodeOthers"], row["PojInputOthers"], multi_others = _others(others)
        multi += multi_others
        for column, values in entry["translations"].items():
            row[column] = LIST_SEPARATOR.join(values)
        row["LaigoanBangchi"] = title_to_url(title)

        counts["readings"] += len(readings)
        counts["readings_annotated"] += sum(1 for _, n in readings if n)
        note_counter.update(n for _, n in readings if n)
        for given in entry["pojt"][:1] if kind == "poj" else []:
            counts["pojt_pages"] += 1
            if not pojt_matches(given, row["PojInput"]):
                counts["pojt_mismatch"] += 1
                lists["pojt_mismatch"].append([title, given, row["PojInput"]])
        entries.append({"title": title, "kind": kind, "row": row, "multi": multi,
                        "corrected": corrected_any})

    entries.sort(key=lambda e: (collation_key(e["row"]["PojUnicode"]), e["title"]))
    rows = [e["row"] for e in entries]
    write_csv(rows, COLUMNS, bunji_dir / f"{TABLE_NAME}.csv")
    write_json_rows(rows, bunji_dir / f"{TABLE_NAME}.json")

    for e in entries:
        multi_counter.update(set(e["multi"]))
    caron_rows = [r["PojUnicode"] for r in rows if _has_caron_on_bearer(r["PojUnicode"])]
    # Assigned, not Counter.update()d: update() would add to a key the page
    # loop had already counted.
    derived = {
        "rows": len(rows),
        "rows_poj_title": sum(1 for e in entries if e["kind"] == "poj"),
        "rows_reading_title": sum(1 for e in entries if e["kind"] == "reading"),
        "rows_text_corrected": sum(1 for e in entries if e["corrected"]),
        "rows_multi_tone": sum(1 for e in entries if e["multi"]),
        "multi_tone_distinct_words": len(multi_counter),
        "rows_caron": len(caron_rows),
        "rows_translated": sum(1 for r in rows if r["EngBun"] or r["HoaBun"] or r["JitBun"]),
        "readings_not_poj": len(lists["readings_not_poj"]),
        "reading_lines_unparsed": len(lists["reading_lines_unparsed"]),
    }
    for column in COLUMNS:
        if column not in ("PojUnicode", "PojInput", "LaigoanBangchi"):
            derived[f"rows_{column}"] = sum(1 for r in rows if r[column])
    derived.update({f"rows_corrected: {name}": n for name, n in correction_counts.items()})
    for key, value in derived.items():
        counts[key] = value
    for key in ("pages_redirect", "pages_index", "pages_poj_not_taigi", "pages_hanji_no_reading",
                "pages_other", "pages_other_dialect_only", "rows_poj_title_with_reading",
                "rows_reading_title_not_hanji", "rows_poj_title_with_hanji", "rows_hanji_multiple",
                "readings", "readings_annotated", "readings_first_annotated",
                "readings_from_nan_pron", "pojt_pages", "pojt_mismatch"):
        counts.setdefault(key, 0)

    ranked = sorted(multi_counter.items(), key=lambda kv: (-kv[1], kv[0]))
    report = {
        "counts": dict(counts),
        "corrections": [[name, correction_counts[name]] for name, _ in TEXT_CORRECTIONS]
                       + [[HYPHENATION, correction_counts[HYPHENATION]]],
        "hyphenated_words": [[w, sp, n] for (w, sp), n in
                             sorted(split_counter.items(), key=lambda kv: (-kv[1], kv[0]))],
        "corrected_rows": lists["corrected_rows"],
        "reading_notes": sorted(note_counter.items(), key=lambda kv: (-kv[1], kv[0])),
        "readings_not_poj": lists["readings_not_poj"],
        "reading_lines_unparsed": lists["reading_lines_unparsed"],
        "hanji_multiple": lists["hanji_multiple"],
        "pojt_mismatch": lists["pojt_mismatch"],
        "multi_tone_words": ranked[:REPORT_SAMPLE_SIZE],
        "multi_tone_words_all": ranked,
        "caron_rows": caron_rows,
        "poj_not_taigi": lists["poj_not_taigi"],
        "hanji_no_reading": lists["hanji_no_reading"],
        "index_pages": lists["index_pages"],
        "redirects": lists["redirects"],
        "skipped_headings": sorted(skipped_headings.items(), key=lambda kv: (-kv[1], kv[0]))[:30],
    }
    write_json(report, report_dir / f"{REPORT_NAME}.json")
    with open(report_dir / f"{REPORT_NAME}.md", "w", encoding="utf-8") as f:
        f.write(render_report_md(report, dump_path.name))

    print(f"  {counts['pages_total']:,} pages → {counts['rows']:,} rows "
          f"({counts['rows_poj_title']:,} from Pe̍h-ōe-jī titles, "
          f"{counts['rows_reading_title']:,} from 臺灣話 readings; "
          f"{counts['rows_HanLoTaibunPoj']:,} with Hanji, "
          f"{counts['rows_text_corrected']:,} with corrected text)")
    return dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dump", help="pages-articles XML dump (.xml.bz2 or .xml)")
    parser.add_argument("bunji_dir", help="output directory for the tables")
    args = parser.parse_args()
    # Titles and arrows must not crash a run on a terminal that is not UTF-8.
    sys.stdout.reconfigure(errors="backslashreplace")
    convert_entries(args.dump, args.bunji_dir)


if __name__ == "__main__":
    main()
