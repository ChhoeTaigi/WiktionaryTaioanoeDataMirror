# WiktionaryTaioanoeDataQuality

Source dump: `zh_min_nanwiktionary-20261001-pages-articles.xml.bz2`

## Counts

|  | count |
|---|---|
| Main-namespace pages in dump | 23,024 |
| Rows published | 16,512 |
| … from a Pe̍h-ōe-jī title | 787 |
| … from a Hanji (or other) title with a 臺灣話 reading | 15,725 |
| … with `HanLoTaibunPoj` | 15,988 |
| … with further readings (`PojUnicodeOthers`) | 3,184 |
| … with a definition (`KaisoehPoj` or `KaisoehHanLoPoj`) | 2,952 |
| … with `EngBun`, `HoaBun` or `JitBun` | 228 |
| … whose text was corrected | 17 |
| … with a multi-tone word | 0 |
| … with a caron on a tone-bearing letter | 1 |

## 1. Pages — which became rows

A page is a Taigi entry when its title is Pe̍h-ōe-jī and it has Taigi
content (a Taigi language heading, a Taigi category, a nan-* template or
a `*臺灣話：` reading), or when its `*臺灣話：` line gives a reading, whatever
the title. Redirects are not rows: their target is. Every other page is
dropped and counted here.

| pages | count |
|---|---|
| Rows: Pe̍h-ōe-jī title with Taigi content | 787 |
| … of which the page also has a `*臺灣話：` reading | 14 |
| Rows: title with a 臺灣話 reading | 15,725 |
| … of which the title is not Hanji | 1 |
| Dropped: redirects | 493 |
| Dropped: Pe̍h-ōe-jī-looking title, no Taigi content (listed below) | 496 |
| Dropped: Hanji title without a 臺灣話 reading | 378 |
| … of which another dialect's line has a reading | 4 |
| Dropped: index and appendix pages | 50 |
| Dropped: entries of other languages | 5,095 |

### Pe̍h-ōe-jī-looking titles with no Taigi content — dropped

Single letters, index pages and words of other languages whose title
happens to parse as Pe̍h-ōe-jī syllables (`ant`, `sin`, `net`).

`Thâu-ia̍h`, `a`, `aⁿ`, `b`, `cH`, `m`, `l`, `h`, `o`, `g`, `cHH`, `e`, `eⁿ`, `iⁿ`, `j`, `k`, `kH`, `ha̍p-im-jī`, `tian-tò ê sû`, `sin hoat-bêng ê iōng-sû`, `dictionary jī-tián a`, `dictionary jī-tián b`, `dictionary jī-tián c`, `dictionary jī-tián d`, `dictionary jī-tián e`, `dictionary jī-tián f`, `dictionary jī-tián h`, `dictionary jī-tián i`, `dictionary jī-tián j`, `dictionary jī-tián k`, `dictionary jī-tián l`, `dictionary jī-tián m`, `dictionary jī-tián n`, `dictionary jī-tián g`, `dictionary jī-tián o`, `dictionary jī-tián p`, `dictionary jī-tián q`, `dictionary jī-tián r`, `dictionary jī-tián s`, `dictionary jī-tián t`, `dictionary jī-tián u`, `dictionary jī-tián v`, `dictionary jī-tián w`, `dictionary jī-tián x`, `dictionary jī-tián y`, `dictionary jī-tián z`, `Hi-sû lia̍t-toaⁿ`, `khin-siaⁿ`, `eng漢POJ jī-tián a`, `eng漢POJ jī-tián b`

496 titles; the first 50 are shown.

### Hanji titles without a 臺灣話 reading — dropped

`奈米`, `果物`, `病気`, `本州`, `言葉`, `海老`, `判子`, `日本語`, `会社`, `試合`, `自転車`, `田舎`, `切符`, `映画`, `背中`, `子供`, `伊勢海老`, `手紙`, `挨拶`, `蜻蛉`, `芝居`, `友達`, `大根`, `身長`, `津波`, `時計`, `花火`, `値段`, `計画`, `怪我`, `井戸`, `人民币`, `人称`, `人类`, `人丁`, `白俄罗斯语`, `澳大利亚`, `澳大利亞`, `阿尔及利亚`, `阿爾及利亞`, `安提瓜和巴布达`, `安提瓜和巴布達`, `亚洲`, `欧洲`, `歐洲`, `白俄羅斯語`, `白俄罗斯`, `白俄羅斯`, `俄羅斯`, `俄罗斯`

378 titles; the first 50 are shown.

### Index and appendix pages — dropped

`pe̍h-ōe-jī Sek-ín`, `Pe̍h-ōe-jī Sek-ín A`, `Pe̍h-ōe-jī Sek-ín B`, `Pe̍h-ōe-jī Sek-ín CH`, `Pe̍h-ōe-jī Sek-ín U`, `Pe̍h-ōe-jī Sek-ín T`, `hù-lio̍k:Sek-tì`, `Sek-ín:Eng漢POJ`, `Pe̍h-ōe-jī Sek-ín Aⁿ`, `Sek-ín:jī-sìⁿ`, `Sek-ín:Kok-ka miâ`, `Sek-ín:Tē-miâ`, `Pe̍h-ōe-jī Sek-ín CHH`, `Pe̍h-ōe-jī Sek-ín TH`, `Pe̍h-ōe-jī Sek-ín E`, `Pe̍h-ōe-jī Sek-ín Eⁿ`, `Pe̍h-ōe-jī Sek-ín O`, `Pe̍h-ōe-jī Sek-ín O·`, `Pe̍h-ōe-jī Sek-ín Oⁿ`, `Pe̍h-ōe-jī Sek-ín M`, `Pe̍h-ōe-jī Sek-ín NG`, `Pe̍h-ōe-jī Sek-ín N`, `Pe̍h-ōe-jī Sek-ín J`, `Pe̍h-ōe-jī Sek-ín G`, `Pe̍h-ōe-jī Sek-ín PH`, `Pe̍h-ōe-jī Sek-ín I`, `Pe̍h-ōe-jī Sek-ín P`, `Pe̍h-ōe-jī Sek-ín Iⁿ`, `Pe̍h-ōe-jī Sek-ín KH`, `Pe̍h-ōe-jī Sek-ín K`, `Pe̍h-ōe-jī Sek-ín S`, `Pe̍h-ōe-jī Sek-ín L`, `Pe̍h-ōe-jī Sek-ín H`, `Sek-ín:Khiuⁿ-kháu`, `Sek-ín:Khiuⁿ-kháu:Bêng-sû`, `Sek-ín:Khiuⁿ-kháu:Hêng-iông-sû`, `Hū-le̍k:Hôa-gú Wikipedia Siông Ēng ê Jī`, `Hū-le̍k:Hôa-gú Wikipedia Siông Ēng ê Jī/2001`, `Hū-le̍k:Hôa-gú Wikipedia Siông Ēng ê Jī/4001`, `Hū-le̍k:Hôa-gú Wikipedia Siông Ēng ê Jī/6001`, `Hū-le̍k:Hôa-gú Wikipedia Siông Ēng ê Jī/Chin-chōe ēng cha̍p-pái`, `Hū-le̍k:Hôa-gú Wikipedia Siông Ēng ê Jī/Chin-chōe ēng nn̄g-pái`, `Hū-le̍k:HSK ê Hôa-gú sû ê chheng-toaⁿ`, `Sek-ín:A-chiu ê tē-miâ`, `Sek-ín:Tiong-hôa Bîn-kok ê tē-miâ`, `Appendix:Unicode/Miscellaneous Symbols and Arrows`, `Appendix:Eng-gí ê hoat-im`, `Appendix:Hiragana`, `Appendix:Katakana`, `Thâu-ia̍hhttps://zh-min-nan.wiktionary.org/wiki/Thâu-ia̍h`

50 titles.

## 2. Text — corrections

`PojUnicode` and the readings are made as good as possible for finding by
Pe̍h-ōe-jī; `LaigoanBangchi` keeps the exact page. These corrections were
made (a row counts once per correction, whichever column it was in):

| correction | rows |
|---|---|
| o· → o͘ | 18 |

Run-together syllables are split only into a hyphenated form that the
wiki's own titles and readings use somewhere, so a foreign name that
happens to parse as syllables is never split.

| page | written | corrected | corrections |
|---|---|---|---|
| `só·-í` | `só·-í` | `só͘-í` | o· → o͘ |
| `鄒` | `Cho·` | `Cho͘` | o· → o͘ |
| `吳` | `Gô·` | `Gô͘` | o· → o͘ |
| `吳` | `Ngô·` | `Ngô͘` | o· → o͘ |
| `許` | `Khó·` | `Khó͘` | o· → o͘ |
| `Eⁿ-go·-lē` | `Eⁿ-go·-lē` | `Eⁿ-go͘-lē` | o· → o͘ |
| `盧` | `Lô·` | `Lô͘` | o· → o͘ |
| `毛` | `Mô·` | `Mô͘` | o· → o͘ |
| `胡` | `Ô·` | `Ô͘` | o· → o͘ |
| `niáu-chhú` | `nó·-chhú` | `nó͘-chhú` | o· → o͘ |
| `chit-sò·` | `chit-sò·` | `chit-sò͘` | o· → o͘ |
| `sng-sò·` | `sng-sò·` | `sng-sò͘` | o· → o͘ |
| `kong-bō·` | `kong-bō·` | `kong-bō͘` | o· → o͘ |
| `thòaⁿ-sò·` | `thòaⁿ-sò·` | `thòaⁿ-sò͘` | o· → o͘ |
| `chúi-sò·` | `chúi-sò·` | `chúi-sò͘` | o· → o͘ |
| `ho·-khip hē-thóng` | `ho·-khip hē-thóng` | `ho͘-khip hē-thóng` | o· → o͘ |
| `hō·-kó` | `hō·-kó` | `hō͘-kó` | o· → o͘ |
| `sò·-kó` | `sò·-kó` | `sò͘-kó` | o· → o͘ |

18 corrected values. All are in `WiktionaryTaioanoeDataQuality.json`.

## 3. Readings — `PojUnicode` and `PojUnicodeOthers` of Hanji pages

The `*臺灣話：` line of a Hanji page gives one reading or several
(`[[jîn]]/[[lîn]], [[lâng]]（替）`), some annotated: 文 literary reading,
替 the Hanji is a substitute character for this reading, 俗/俗音 popular
pronunciation, 合音 contraction, 又音/又唸作 also read. The first reading
is `PojUnicode`; the rest are `PojUnicodeOthers`, each with its note in
parentheses, joined with `/` — the format KauiokPooSutian uses for the
same Ministry of Education data. A first reading that carries a note is
repeated in `PojUnicodeOthers` with it, since the note has no column of
its own.

|  | count |
|---|---|
| Readings published | 19,092 |
| … with a note | 1,169 |
| First readings with a note (repeated in `PojUnicodeOthers`) | 348 |
| Readings taken from a nan-pron template (no 臺灣話 line) | 11 |
| Readings not in Pe̍h-ōe-jī spelling (listed below) | 27 |
| Reading lines with text that could not be read (listed below) | 0 |

| note | readings |
|---|---|
| `文` | 538 |
| `替` | 526 |
| `俗` | 23 |
| `合音` | 10 |
| `qz` | 6 |
| `zz` | 6 |
| `俗音` | 6 |
| `twv` | 4 |
| `tw` | 2 |
| `xm,tp` | 2 |
| `zz,kh` | 2 |
| `zz,twv` | 2 |
| `又唸作` | 2 |
| `泉` | 2 |
| `漳腔` | 2 |
| `jj,ph` | 1 |
| `kh` | 1 |
| `ml,tw,pn` | 1 |
| `pn` | 1 |
| `qz,ph` | 1 |
| `qz,tw` | 1 |
| `qz,tw,xm` | 1 |
| `qz,twv` | 1 |
| `sx,qz,km` | 1 |
| `tn,lk` | 1 |
| `tp,kh,tn,lk,sx,yl,hc,tc` | 1 |
| `tw,xm` | 1 |
| `twq` | 1 |
| `twq,ta,ph,pn,sg` | 1 |
| `twq,xm,qz` | 1 |
| `twvk` | 1 |
| `twvt` | 1 |
| `twz` | 1 |
| `twz,xm,zz` | 1 |
| `twz,zz` | 1 |
| `xm` | 1 |
| `xm,km,twv` | 1 |
| `xm,qz,tp` | 1 |
| `xm,qz,tw` | 1 |
| `xm,qz,zz,tw` | 1 |
| `xm,tw,zz` | 1 |
| `xm,zz,tw` | 1 |
| `xm,zz,tw,pn` | 1 |
| `xm,zz,twv,pn` | 1 |
| `俗、替` | 1 |
| `前者音變` | 1 |
| `又音` | 1 |
| `合` | 1 |
| `日語予備借音` | 1 |
| `替、文` | 1 |
| `白話` | 1 |

### Readings not in Pe̍h-ōe-jī spelling — published as written

KPL spellings (`oo`, `nn`, `ts`), tone numbers or other slips; the
mirror is faithful and does not correct them.

| page | reading |
|---|---|
| `向` | `ànn` |
| `哥` | `kő` |
| `昨昏` | `cha̋ng` |
| `清代` | `Tsheng-tāi` |
| `呼` | `honn` |
| `親情五十` | `chhin-chiânn-gō͘-cha̍p` |
| `揤` | `tshi̍h` |
| `來去` | `la̋i` |
| `心驚膽嚇` | `sim-kiaⁿ-táⁿ-hiahⁿ` |
| `猴齊天` | `Kâu Tsê-thian` |
| `註生娘娘` | `Tsù-seⁿ-niû-niû` |
| `註生娘娘` | `Tsù-siⁿ-niû-niû` |
| `連鞭` | `liâm-pinn` |
| `查某囝` | `cha̋u-kiáⁿ` |
| `澩澩` | `ha̍uhⁿ-ha̍uhⁿ` |
| `無要緊` | `boa̋-kín` |
| `貨` | `hònn` |
| `抑是` | `á-sǐ` |
| `轎車椅` | `kiǒ-chhia-í` |
| `胭脂茄` | `ian-chsi-kiô` |
| `頓` | `tuìnn` |
| `回朝` | `hhê-tiâu` |
| `準拄煞` | `tsún-tú-soah` |
| `食人夠夠` | `tsia̍h-lâng-kàu-kàu` |
| `𠢕早` | `gâu-tsá` |
| `烏天暗地` | `oo-thinn-àm-tē` |
| `烏天暗地` | `oo-thinn-àm-tuē` |

27 readings.

### Reading lines with text that could not be read

| page | line | not read |
|---|---|---|

0 lines.

## 4. Hanji of Pe̍h-ōe-jī pages — `HanLoTaibunPoj`

From the `tas=` (漢), `tra=` (繁) or `orig=` (本) parameter of the page's
nan-* templates, then from its `Hàn-jī` section. Several forms are
joined with `/`.

|  | count |
|---|---|
| Pe̍h-ōe-jī pages with Hanji | 263 |
| … with more than one form (listed below) | 10 |
| Pe̍h-ōe-jī pages without Hanji | 524 |

| page | `HanLoTaibunPoj` |
|---|---|
| `lâng` | `人/儂/聾` |
| `bâng` | `毋通/嘜` |
| `tōng-bu̍t-hn̂g` | `動物圂/動物園` |
| `ka` | `家/鳩/鉸/加` |
| `lâm` | `藍/南` |
| `tan-to̍k` | `丹毒/單獨` |
| `tiān-ōe` | `電話/电话` |
| `am-khàm` | `掩崁/掩蓋` |
| `kun-goân` | `根原/根源` |
| `thoân-thóng` | `傳統/伝統` |

10 pages.

## 5. Multi-tone words — `PojInput` left unconverted

A Pe̍h-ōe-jī syllable carries at most one tone mark. A word with two or
more that could not be split into syllables is copied into `PojInput`
as written rather than guessed at.

### Caron on a tone-bearing letter — left as written

A caron (`ǔ`, `ě`) is not read as a tone mark, as in KonvertToPOJ.

`kiǒ-chhia-í`

1 row.

## 6. The page's own ASCII spelling — `pojt=` against `PojInput`

Pe̍h-ōe-jī pages with a nan-* template give their own tone-number
spelling (`pojt=chhiu2`, writing ⁿ as `N` and o͘ as `ou`). Where it
disagrees with `PojInput`, one of the two is wrong on the page; nothing
is changed here.

|  | count |
|---|---|
| Pages with a `pojt=` | 150 |
| … agreeing with `PojInput` | 146 |
| … differing (listed below) | 4 |

| page | `pojt=` | `PojInput` |
|---|---|---|
| `chôa` | `choa3` | `choa5` |
| `gí-giân` | `gí-giân, gú-giân, gý-giân` | `gi2-gian5` |
| `Tiong-hôa Jîn-bîn Kiōng-hô-kok Hiong-káng Te̍k-pia̍t Hêng-chèng-khu` | `Tiong-hoa5 Jin5-bin5 Kiong5-ho5-kok Hiong-kang2 Tek8-piat8 Heng5-cheng3-khu` | `Tiong-hoa5 Jin5-bin5 Kiong7-ho5-kok Hiong-kang2 Tek8-piat8 Heng5-cheng3-khu` |
| `Soviet Siā-hōe-chú-gī Kiōng-hô-kok Liân-ha̍p` | `Soviet Siā-hōe-chú-gī Kiōng-hô-kok Liân-ha̍p` | `Soviet Sia7-hoe7-chu2-gi7 Kiong7-ho5-kok Lian5-hap8` |

4 pages.

## 7. Definitions, parts of speech and translations

From the Taigi section of each page: the lines of its part-of-speech
and `Kái-soeh`/`意思` sections are `KaisoehPoj` (Pe̍h-ōe-jī pages) or
`KaisoehHanLoPoj` (Hanji pages), one per line, examples left out; the
part-of-speech headings and templates give `Hunlui`; the `Eng-gú`,
`Hôa-gú` and `Ji̍t-gí` lines of its translation table give `EngBun`,
`HoaBun` and `JitBun`, markup and romanisations dropped.

| column | rows |
|---|---|
| `Hunlui` | 714 |
| `KaisoehPoj` | 741 |
| `KaisoehHanLoPoj` | 2,211 |
| `EngBun` | 208 |
| `HoaBun` | 188 |
| `JitBun` | 178 |

### Section headings in Taigi entries that were not used

Sections other than definitions, Hanji and translations are not read
(examples, proverbs, references, KPL spelling…). The most frequent:

| heading | pages |
|---|---|
| `音` | 15,718 |
| `Lē-kù` | 275 |
| `Kàu-io̍k-pō͘ peng-im` | 235 |
| `Chham-khó` | 172 |
| `Chham-khó Lâi-goân` | 100 |
| `Sio̍k-gí` | 85 |
| `相siâng` | 78 |
| `Chham-khó 參考` | 16 |
| `Khiuⁿ-kháu` | 13 |
| `參考資料` | 12 |
| `Lēkù` | 10 |
| `字源` | 8 |
| `發音` | 5 |
| `Siong-koan` | 4 |
| `Sû-goân` | 4 |
| `sio̍k-gí` | 4 |
| `外部連結` | 4 |
| `Gān-gí` | 3 |
| `Kî-tha sû-tián` | 3 |
| `Tha̍k` | 3 |
| `例` | 3 |
| `Chham-khó lâi-goân` | 2 |
| `Khiuⁿ-káu` | 2 |
| `Lē` | 2 |
| `Miâ-sû` | 2 |
| `Ōe-kù` | 2 |
| `異用字` | 2 |
| `Chham-kiàn` | 1 |
| `Ha̍p-sêng-sû` | 1 |
| `Hoat-im` | 1 |

Full lists are in `WiktionaryTaioanoeDataQuality.json`.
