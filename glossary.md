# Glossary - Ganbare! Daiku no Gen-san (SNES, Irem 1993)

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
`tools/batches.py check` enforces the EN column for every JP term present in an entry.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Gen-san, Kanna-chan, Genzo-kun). Name order: Western (given name first) (D1).
- Romanisation: official English names where they exist, else Hepburn without macrons (D2). The series is
  *Hammerin' Harry* abroad, but this game's own cast is named in kana/kanji: we keep the Japanese names.
- Credits: English, Western order, Hepburn without macrons (Kato Yuichi -> YUICHI KATO) (D3).
- Register: comic Edo-style tough-guy carpenter story for kids; light Japanese flavour (honorifics, "Teyandei!").
- Abbreviations: none (D4). If a line can't fit, report `LONG:`; the controller does engine work.

## Style rules
- Punctuation: ‼ -> `!!`, ！？ -> `!?`, … / …… -> `...`, 、 -> `,` or nothing, 「」 -> "...".
- Gen-san: rough, cocky Edo carpenter (べらんめえ talk): short punchy lines, "Teyandei!" as his catchphrase
  (てやんでい, a Tokyo-workman's "Like heck!"), says "Gen" or "I" about himself, threatens to "hammer some sense"
  into villains (改心させてやる = make them reform/turn over a new leaf).
- 改心 (the game's key word, in most chapters and the final card): Gen-san beats villains until they reform. Use
  "reform" / "go straight" / "mend your ways" / "turn over a new leaf" as the line needs, never "repent".
- Kanna-chan: sweet, a bit spoiled; calls him "Gen-san".
- Kuromoku Gang members: blustering; the Kansai thug (chapter 1-2) speaks rough Kansai: a slangy, brash voice in
  English ("Ain't no way I'm losin'!"), not phonetic spelling.
- Narrator (book pages, ticker): cheerful, cheering Gen on ("Don't give up, Gen-san!").

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 源さん | Gen-san | | the hero, a carpenter | Harry, Gen-sama |
| 源 | Gen | | bare name, used by friends and rivals | |
| 源三 | Genzo | | his full given name (源三くん = Genzo-kun) | Genzou, Genzō |
| カンナちゃん | Kanna-chan | | Gen-san's girlfriend; kidnapped in chapter 4 | Kanna |
| 黒木組 | Kuromoku Gang | | the rival construction outfit / gang (read くろもく, see stage name) | Kuroki, Kurogi |
| 社長 | the Boss | | head of the Kuromoku Gang (literally the company president); capital B | president, CEO |
| らいぞう | Raizo | | final stage / final opponent's name (stage name only) | Raizou |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| てやんでちょう | TEYANDE | 9 | stage 1, Teyande Town (pun on てやんでい + 町); HUD has 9 cells after "1-1 " | |
| べらんめしんりん | BERANME | 9 | stage 2, Beranme Woods (pun on べらんめえ + 森林) | |
| が[F7]てんだに | GATTEN | 9 | stage 3, Gatten Valley (がってん "gotcha!" + 谷) | |
| くろもくアジト | KUROMOKU | 9 | stage 4, the Kuromoku hideout | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 木づち | mallet | | Gen-san's giant wooden mallet (his weapon) | hammer |
| 序章 | Prologue | | chapter card label | |
| 終章 | Finale | | chapter card label | Epilogue |

## Decisions from earlier batches
- b002 N章前編 / N章後編 -> "Chapter N-1" / "Chapter N-2" (cards; matches the HUD's stage numbers; no colon after the
  label: `Chapter 1-1 Guard the Town!!`, `Prologue ...`, `Finale ...`).
- b001 改心しやがれ -> "Mend your ways!" (script8.3, script9.1, card13).
- b001 女大工 -> "woman carpenter" (script4.0, split over two panels with {page}).
- b003 ｺﾝｼｭｰﾏ / ｱｰｹｰﾄﾞ / ｱﾒﾘｶﾝ ｽﾀｯﾌ -> CONSUMER / ARCADE / AMERICAN STAFF; "&" kept in credit role names (as the JP).
- b003 ﾋﾗｼﾏ ﾘｹｲ -> RIKEI HIRASHIMA (literal kana reading; unconfirmed).
