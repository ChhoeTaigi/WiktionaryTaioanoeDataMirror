"""Pe̍h-ōe-jī text handling shared by the ChhoeTaigi Wikimedia mirrors.

Ported from WikipediaPehoejiDataMirror's convert_titles.py so this mirror
selects and renders Pe̍h-ōe-jī exactly as the Wikipedia one does: the same
syllable regex decides whether a title is Pe̍h-ōe-jī, the same conversion
produces the tone-number input form, and the same corrections make the text
searchable. Every oddity kept here is deliberate; see "Non-obvious
invariants" in CLAUDE.md before changing anything.
"""
import functools
import itertools
import re
import sys
import unicodedata

# --- Selection --------------------------------------------------------------

# Ported verbatim from ParseWikipediaPehoejiPanAllTitlesInNamespace0
# (src/main/kotlin/wiktionary/Main2.kt, the same regex as its Wikipedia twin)
# so this mirror selects exactly the titles ChhoeTaigi has always ingested. It matches ONE syllable, applied
# case-insensitively to each segment of the title split on `-`, `_`, `(`, `)`.
# A title is kept if ANY segment is a syllable. Kept as-is, oddities included
# (`̍ă` with a leading combining mark, `r` as a vowel): changing it changes
# which titles are published. See "Non-obvious invariants" in CLAUDE.md.
# `o\u0324\u0306` (ŏ̤) is escaped because Kotlin's is decomposed, and an editor
# that NFC-normalizes would silently turn it into the different `ŏ̤`.
POJ_UNICODE_REGEX = (
    "^(ph|p|m|b|th|t|l|kh|k|ng|n|g|h|chh|ch|s|j)?"
    "((?:á|à|â|ā|a̍|̍ă|a|í|ì|î|ī|i̍|ĭ|i|ṳ́|ṳ̀|ṳ̂|ṳ̄|ṳ̍|ṳ̆|ṳ|ú|ù|û|ū|u̍|ŭ|u"
    "|ó͘|ò͘|ô͘|ō͘|o̍͘|ǒ͘|o͘|ó̤|ò̤|ô̤|ō̤|o̤̍|o\u0324\u0306|o̤|é|è|ê|ē|e̍|ĕ|e|ó|ò|ô|ō|o̍|ŏ|o|r)*)"
    "(ⁿ|ḿ|m̀|m̂|m̄|m̍|m̆|m|ńg|ǹg|n̂g|n̄g|n̍g|n̆g|ng|ń|ǹ|n̂|n̄|n̍|n̆|n)?"
    "(p|t|k|h)?$"
)
POJ_SYLLABLE = re.compile(POJ_UNICODE_REGEX, re.IGNORECASE)
SEGMENT_SPLIT = re.compile(r"[\-_()]")


def contains_poj(title):
    """True when any `-`/`_`/`(`/`)` segment of title is a POJ syllable."""
    return any(seg and POJ_SYLLABLE.match(seg) for seg in SEGMENT_SPLIT.split(title))


# --- Pe̍h-ōe-jī Unicode → input form -----------------------------------------

# Tone diacritics (NFD combining marks) → tone number, as in KonvertToPOJ's
# ToneMap: breve is tone 9 (not 6), and `n` takes the double acute for 9.
TONE_MARKS = {
    "́": "2",  # acute
    "̀": "3",  # grave
    "̂": "5",  # circumflex
    "̄": "7",  # macron
    "̍": "8",  # vertical line above
    "̆": "9",  # breve
    "̋": "9",  # double acute (n̋)
}
# A caron is not a POJ tone mark here, as in KonvertToPOJ: on a tone bearer it
# is left as written (Czech `Moravě`, but also Taigi `jiǔ`), and such rows are
# listed in the report so they stay visible.
CARON = "\u030c"
# Only these letters bear a POJ tone. A mark on anything else (ś, ž, ư, ý) is
# another language's diacritic and is left untouched.
TONE_BEARERS = set("aeioumnAEIOUMN")
# Non-tone POJ marks, rewritten to their input spelling.
DOT_ABOVE_RIGHT = "͘"   # o͘  → oo
DIAERESIS_BELOW = "̤"   # ṳ, o̤ → ur, or
SUPERSCRIPT_N = "ⁿ"          # ⁿ  → nn
POJ_EXTRA_MARKS = {DOT_ABOVE_RIGHT, DIAERESIS_BELOW}

# A word is a run of letters AND combining marks: Python's \w excludes
# combining marks, so without them `ji̍t` would split into `ji` + `̍` + `t`.
# Every combining mark (category M), in whatever Unicode block, not just
# U+0300–036F: a mark from any other block would split a word the same way.
def _mark_class():
    ranges, start = [], None
    for cp in range(sys.maxunicode + 2):
        is_mark = cp <= sys.maxunicode and unicodedata.category(chr(cp)).startswith("M")
        if is_mark and start is None:
            start = cp
        elif not is_mark and start is not None:
            ranges.append(f"{re.escape(chr(start))}-{re.escape(chr(cp - 1))}")
            start = None
    return "".join(ranges)


WORD = re.compile(r"(?:[^\W\d_]|[" + _mark_class() + r"])+")


@functools.lru_cache(maxsize=None)
def _is_latin(ch):
    """Latin letters, the modifier letters written among them (ⁿ, ʾ) and
    combining marks: the part of a word a tone number goes after. Han right
    after a syllable (`ló話`) is not part of it, or the number would land
    after the Han (`lo話2`)."""
    return (unicodedata.category(ch) in ("Lm", "Mn", "Mc", "Me")
            or "LATIN" in unicodedata.name(ch, ""))


def _clusters(word):
    """Split an NFD word into (base, [combining marks]) clusters."""
    clusters = []
    for ch in unicodedata.normalize("NFD", word):
        if unicodedata.combining(ch) and clusters:
            clusters[-1][1].append(ch)
        else:
            clusters.append((ch, []))
    return clusters


def _is_poj_letter(base, marks):
    """True when base+marks is a POJ letter: a tone bearer with at most one
    tone mark and no mark POJ does not use. Vietnamese ộ, ễ, ắ (a second mark
    stacked on the tone) and ư, ơ (horn) are someone else's letters."""
    if base not in TONE_BEARERS:
        return False
    if any(m not in TONE_MARKS and m not in POJ_EXTRA_MARKS for m in marks):
        return False
    if DOT_ABOVE_RIGHT in marks and base not in "oO":
        return False
    return sum(m in TONE_MARKS for m in marks) <= 1


def word_to_input(word):
    """One word → (input form, is_multi_tone).

    A POJ syllable carries at most one tone mark. A word with two or more
    (`kūle̍k`, `Lō͘sòaⁿ` — syllables written without their hyphen) has no
    single tone number to append, so it is returned unchanged and flagged
    rather than guessed at.
    """
    clusters = _clusters(word)
    tones = [
        m for base, marks in clusters if _is_poj_letter(base, marks)
        for m in marks if m in TONE_MARKS
    ]
    if len(tones) > 1:
        return word, True

    out = []
    for base, marks in clusters:
        poj_letter = _is_poj_letter(base, marks)
        piece = base
        for m in marks:
            if poj_letter and m in TONE_MARKS:
                continue
            if poj_letter and m == DOT_ABOVE_RIGHT:
                piece += "o"
            elif poj_letter and m == DIAERESIS_BELOW:
                piece += "r"
            else:
                piece += m
        out.append(piece)
    text = unicodedata.normalize("NFC", "".join(out)).replace(SUPERSCRIPT_N, "nn")
    return text + (TONE_MARKS[tones[0]] if tones else ""), False


def _has_caron_on_bearer(text):
    return any(base in TONE_BEARERS and CARON in marks for base, marks in _clusters(text))


def poj_unicode_to_input(text):
    """`Tâi-oân-hú-siâⁿ` → `Tai5-oan5-hu2-siann5`. Returns (input, multi_tone_words)."""
    multi = []

    def convert(run):
        converted, is_multi = word_to_input(run)
        if is_multi:
            multi.append(run)
        return converted

    def repl(m):
        # Only the Latin runs of a word are converted; Han, kana, Hangul… pass.
        return "".join(convert("".join(run)) if latin else "".join(run)
                       for latin, run in itertools.groupby(m.group(0), key=_is_latin))

    return WORD.sub(repl, text), multi


def _tone_count(run):
    return sum(m in TONE_MARKS for base, marks in _clusters(run)
               if _is_poj_letter(base, marks) for m in marks)


# --- Title text ---------------------------------------------------------------

# PojUnicode is the title made as good as possible for finding by Pe̍h-ōe-jī:
# ChhoeTaigi searches it. LaigoanBangchi keeps the exact page, so the text is
# free to differ from the title; every correction is listed in the report.

# `·` (or `•`) right after an o is the dot of o͘ typed as a character of its
# own: `Chúi-lō·` is `Chúi-lō͘`. Elsewhere `·` separates words (`Sam·It`).
O_WITH_DOT = re.compile("([oOòóôōŏǒÒÓÔŌŎǑ]\u030d?)[\u00b7\u2022]")
# i̍ typed with a dotless ı, so the vertical line need not sit on a dot
# (`Jı̍t-pún`), or with Greek ἰ (`jἰt`). In NFD. Plain ı (Turkish) stays.
TONED_DOTLESS_I = re.compile("\u0131(?=[\u0300-\u030f])")
# ἰ only beside a Latin letter, and with no further mark: genuine Greek
# (`Αἰσχύλος`, `Αἴγινα`) is left alone.
GREEK_I_WITH_PSILI = re.compile("(?<=[A-Za-z])\u03b9\u0313(?![\u0300-\u036f])"
                                "|\u03b9\u0313(?=[A-Za-z])")
HYPHEN_LOOKALIKES = re.compile("[\u2010\u2011]")
FULLWIDTH_ASCII = re.compile("[\uff01-\uff5e]")
# `(` stuck to a word gets the space every other title has before it, unless
# it is notation: `tâng(II)`, `501(c)`.
ATTACHED_PAREN = re.compile(
    r"(?:(?<=[^\W\d_])|(?<=[\u0300-\u036f]))\((?!(?:[IVXLCDM]+|[A-Za-z])\))")

# Syllables run together in one word (`kūle̍k`, `Lō͘sòaⁿ`) are split again —
# into a hyphenated form the wiki's own titles and readings use somewhere
# (`kū-le̍k`), and
# only then: foreign names that happen to parse as syllables (`Hélène` →
# `Hé-lè-ne`) never appear so, and the form in use also decides between two
# parses (`sîtāi`: `sî-tāi`, not `sît-āi`). Only words with a tone mark that
# are not themselves one syllable are split: `hiông` stays, `Sūkhek` does not.
POJ_INITIALS = ("", "p", "ph", "m", "b", "t", "th", "n", "l", "k", "kh", "ng", "g",
                "h", "ch", "chh", "s", "j")
# Finals in a key alphabet where O is o͘ and N is ⁿ.
_VOWEL_FINALS = ("a", "ai", "au", "e", "i", "ia", "iau", "io", "iu", "o", "O", "oa",
                 "oai", "oe", "u", "ui")
POJ_FINALS = {v + c for v in _VOWEL_FINALS for c in ("", "h", "N", "Nh")} | {
    "am", "ap", "an", "at", "ang", "ak", "iam", "iap", "ian", "iat", "iang", "iak",
    "im", "ip", "in", "it", "eng", "ek", "iong", "iok", "om", "op", "ong", "ok",
    "oan", "oat", "oang", "un", "ut", "Om", "Ong", "Ok"}
# The syllabic nasals take any initial too: mn̂g, tn̂g, sng, kng, pn̄g, nńg.
POJ_SYLLABLES = ({i + f for i in POJ_INITIALS for f in POJ_FINALS}
                 | {i + n for i in POJ_INITIALS for n in ("m", "mh", "ng", "ngh")})
_LONGEST_SYLLABLE = max(map(len, POJ_SYLLABLES))
ATTESTATION_TOKEN = re.compile(r"[^\s_(),./:;!?\"“”'‘’]+")


def attested_hyphenations(titles):
    """Every run of hyphen-joined pieces in the hyphenated words of titles,
    lowercased: `Tiong-kok-Kiōng-sán-tóng` gives `kiōng`, `kiōng-sán`,
    `kiōng-sán-tóng`, … A split is used only when it is one of these, and so
    is every split's beginning, which keeps the search for one short."""
    out = set()
    for title in titles:
        for token in ATTESTATION_TOKEN.findall(title):
            pieces = [p for p in unicodedata.normalize("NFC", token.lower()).split("-") if p]
            if len(pieces) < 2:
                continue
            for i in range(len(pieces)):
                for j in range(i + 1, len(pieces) + 1):
                    out.add("-".join(pieces[i:j]))
    return out


def _syllable_keys(word):
    """[(key, has tone, letters)] per letter of word, or None when a letter is
    not one POJ writes."""
    keys = []
    for base, marks in _clusters(word):
        if base == SUPERSCRIPT_N and not marks:
            keys.append(("N", False, base))
            continue
        low = base.lower()
        if low not in "abceghijklmnopstu" or (marks and not _is_poj_letter(low, marks)):
            return None
        keys.append(("O" if DOT_ABOVE_RIGHT in marks else low,
                     any(m in TONE_MARKS for m in marks), base + "".join(marks)))
    return keys


def _is_one_syllable(keys):
    return ("".join(k for k, _, _ in keys) in POJ_SYLLABLES
            and sum(t for _, t, _ in keys) <= 1)


def _attested_splits(keys, attested):
    """Every split of keys into POJ syllables of at most one tone each whose
    hyphenated form is in attested, built only through attested beginnings:
    a word with no attested split costs a few steps, not every parse."""
    out = []

    def walk(i, parts):
        if i == len(keys):
            out.append("-".join(parts))
            return
        for j in range(i + 1, min(len(keys), i + _LONGEST_SYLLABLE) + 1):
            piece = keys[i:j]
            if not _is_one_syllable(piece):
                continue
            so_far = parts + [unicodedata.normalize("NFC", "".join(t for _, _, t in piece))]
            if "-".join(so_far).lower() in attested:
                walk(j, so_far)

    walk(0, [])
    return [s for s in out if "-" in s]


def hyphenate(word, attested):
    """word with hyphens between its syllables, when it is not itself one
    syllable and exactly one split of it is a hyphenated form in attested;
    otherwise None."""
    keys = _syllable_keys(word)
    if not keys or _is_one_syllable(keys):
        return None
    found = set(_attested_splits(keys, attested))
    return found.pop() if len(found) == 1 else None


def _ascii_punctuation(text):
    """`（…）！？，` → `(…)!?,`, with the space a following Latin letter needs
    after `!?,.;:` (`Ha--looh！Tâi-uân` → `Ha--looh! Tâi-uân`)."""
    def repl(m):
        ch = chr(ord(m.group(0)) - 0xFEE0)
        nxt = m.string[m.end():m.end() + 1]
        return ch + (" " if ch in "!?,.;:" and nxt and _is_latin(nxt) else "")
    return FULLWIDTH_ASCII.sub(repl, text)


def _dotted_i(text):
    nfd = unicodedata.normalize("NFD", text)
    fixed = GREEK_I_WITH_PSILI.sub("i\u030d", TONED_DOTLESS_I.sub("i", nfd))
    return text if fixed == nfd else unicodedata.normalize("NFC", fixed)


# (name, function) in the order applied; the names are what the report lists.
TEXT_CORRECTIONS = [
    ("full-width punctuation → ASCII", _ascii_punctuation),
    ("o· → o͘", lambda t: O_WITH_DOT.sub(r"\1" + DOT_ABOVE_RIGHT, t)),
    ("ı̍ / ἰ → i̍", _dotted_i),
    ("non-breaking hyphen → -", lambda t: HYPHEN_LOOKALIKES.sub("-", t)),
    ("space before (", lambda t: ATTACHED_PAREN.sub(" (", t)),
]
HYPHENATION = "hyphens between run-together syllables"


def title_text(title, attested):
    """(PojUnicode for title, [names of the corrections made], [(word, split)]).
    `_` is a space, so `Tâi-oân-koān_(1684~1887)` → `Tâi-oân-koān (1684~1887)`.
    Applied to titles and to the readings on Hanji pages alike."""
    text = title.replace("_", " ")
    made = []
    for name, correct in TEXT_CORRECTIONS:
        fixed = correct(text)
        if fixed != text:
            made.append(name)
            text = fixed

    splits = []

    def repl(m):
        out = []
        for latin, run in itertools.groupby(m.group(0), key=_is_latin):
            run = "".join(run)
            # A word with a tone mark is split when it is not one syllable:
            # `Sūkhek` would otherwise get its number after `khek` (`Sukhek7`).
            if latin and _tone_count(run):
                split = hyphenate(run, attested)
                if split:
                    splits.append((run, split))
                    run = split
            out.append(run)
        return "".join(out)

    text = WORD.sub(repl, text)
    if splits:
        made.append(HYPHENATION)
    return text, made, splits




# --- Readings -----------------------------------------------------------------

# A reading is checked syllable by syllable: split on hyphens (`--` for a
# neutral tone too) and spaces, each piece must be one Pe̍h-ōe-jī syllable.
READING_SPLIT = re.compile(r"[\s\-]+")


def is_poj(text):
    """True when every syllable of text matches the Pe̍h-ōe-jī syllable regex.
    KPL spellings (`oo`, `nn`, `ts`), tone numbers and Hanji fail it."""
    pieces = [p for p in READING_SPLIT.split(text) if p]
    return bool(pieces) and all(POJ_SYLLABLE.match(p) for p in pieces)


def collation_key(text):
    """Sort key that orders by base letters first (`á` beside `a`), then by
    the exact string, so the tables sort the same on every run."""
    base = "".join(ch for ch in unicodedata.normalize("NFD", text)
                   if not unicodedata.combining(ch))
    return (base.casefold().replace(SUPERSCRIPT_N, "nn"), text)
