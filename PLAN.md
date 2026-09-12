# Autocomplete word game — v1 plan

Build spec only. Do not treat this file as the app. Implementation has not started.

A mobile-first web game: a short English word starts with one letter shown. The rest fill in left to right on a fixed timer. You type the word in one field. Matching it wins the round instantly. If the board finishes the word, you lose. Score is how many words you get before the first miss. Nothing is saved.

This is a race against an autocomplete, not Wordle.

---

## Locked decisions

| Topic | Decision |
|---|---|
| Input | Model B: read-only puzzle + one always-focused guess field |
| Win | Instant match. No Submit required to succeed |
| Lose | Last letter is revealed and the field does not already match |
| Pre-reveal | Before **any** letter is painted, check the field. Match → win and do **not** paint that letter |
| Edit | Backspace allowed. Cannot delete the locked revealed prefix |
| Type-ahead | Allowed. Letters not yet revealed may be typed |
| Wrong letter | Not an instant miss. It simply fails to match until fixed |
| Keyboard | Native OS keyboard on touch devices. Mic is whatever that keyboard already offers |
| Voice | No custom Speech Recognition API in v1 |
| Length | Chosen once at start: 4 easy, 5 medium, 6 hard. Never mixed in a run |
| Words | Curated playable lists, ranked common → uncommon. No live dictionary API at runtime |
| Profanity | None. Strip slurs, sexual terms, strong profanity |
| Language | US English, `A–Z` only. No accents |
| Difficulty in a run | Words get rarer. Timer does **not** speed up |
| Timer | Fixed interval. Recommended first value: **1.8s per letter**, all modes |
| Last letter | Revealing it is immediate fail. No grace period after the word is visible |
| Score | Streak until first miss. Not stored |
| Visual | Super minimal. Atkinson Hyperlegible Next. Phantasm-adjacent, not Wordle. Utilitarian |
| Stack | Vite + Svelte 5 + TypeScript. No UI kit |
| Host | Cloudflare Workers static assets via Wrangler. Not Vercel. Not Next.js |

---

## Why this game

The pieces exist separately. This combination does not look like a known hit.

- **Ten Words Unlocked** is the closest: first letter visible, more letters over time, last letter often not auto-filled. It is a daily 10-word topic quiz with a shared clock, not an endless streak against a left-to-right autocomplete.
- **Lingo** gives the first letter of a 5-letter word, then you spend guesses. The word does not type itself.
- **Heardle / Framed** are the same *shape* (guess before the reveal finishes) on song/image, not letters.
- Hangman / Wordle are the opposite direction: you earn letters or propose full words.

Do not clone Ten Words Unlocked. The product here is: endless run, one length per session, rising rarity, input speed as the skill.

---

## Core tension

Early, you do not have enough letters to know the word. Late, you know it and must get it into the field before the next paint.

Version 1 is about making “I know it” register in a fraction of a second on a phone. If that is slow, later rounds feel like a typing test.

---

## Stack and hosting

**Use:** Vite + Svelte 5 + TypeScript.

**Do not use:** Next.js, Vercel, shadcn, or any component library.

This is one screen, static JSON, a timer, and a text field. Next was an early generic default for “new web app.” It is the wrong tool here. joris.wtf is Astro/Svelte with Atkinson on Cloudflare. Phantasm is a Vite bundle on Cloudflare. Match that family.

```text
Vite + Svelte 5 + TypeScript
Atkinson Hyperlegible Next (self-hosted .woff2)
No UI kit
src/data/words/{4,5,6}.json
scripts/build-wordlists.py   # dev only, not runtime
wrangler.jsonc               # Workers static assets
```

Local: Vite on an uncommon port (not 3000 / 5173 / 8080).

Ship:

```text
vite build
wrangler deploy
```

Point Wrangler `[assets]` at `dist`. No OpenNext. No Node server. No API routes.

Live host: Cloudflare Workers static assets, likely a `*.joris.wtf` subdomain next to Phantasm, Autobahn, etc. Domain is not part of v1 code.

---

## Game loop

### Start

One screen: `4` / `5` / `6`, then **Start**.

Start is a real tap. iOS often will not open the keyboard on page-load focus. Start both focuses the field and starts the timer.

### Play layout (mobile first)

- Top: score as a number. Optional quiet timer if it stays utilitarian; do not add a dashboard.
- Upper third: the word as type, first letter filled, rest empty or dim. Not candy Wordle tiles.
- Under that: one guess field, focused, first letter filled and locked.
- Native keyboard. Attributes:

```html
autocorrect="off"
autocomplete="off"
spellcheck="false"
autocapitalize="characters"
maxlength={n}
```

Everything lives in the visual viewport above the keyboard.

### Reveal

Letters fill **left to right** on a **constant** interval (1.8s unless playtest changes it). Same interval in 4/5/6. Six letters is already harder (more to see, more to type, rarer list).

### Win

Normalized input equals the word → score +1, next word immediately, **do not blur** (or iOS kills the keyboard). Next word from a rarer band.

### Lose

Last letter is painted without a match → overlay: the word, the streak, Play again (same length). Changing length goes back to the start screen.

### Background

Timer pauses when the tab is hidden. Resume only on tap, so the keyboard can come back.

---

## Input rules

Model B: tiles/type are the puzzle. They are not per-cell inputs. One field captures all keystrokes.

1. Case-insensitive. Strip non-letters (spaces from dictation, punctuation). Compare to the target.
2. `maxLength` = word length.
3. First letter is prefilled and locked.
4. As letters reveal, the **revealed prefix is locked in the field and grows**.
5. Type-ahead past that prefix is kept if it still matches the word so far.
6. If a new reveal **contradicts** type-ahead, snap the field back to the revealed prefix. That is a correction, not a loss.
7. Backspace cannot delete the locked prefix.
8. Instant match on every input event. Do not wait for Enter or Submit. A visible Submit is out of v1.
9. Between words: clear type-ahead, set the new first letter, **keep focus**.
10. Paste is sanitized to `A–Z` and truncated to `n`.

Dictation (OS keyboard mic) may dump a whole word, a space, or odd casing. Sanitize and still instant-match. It will often be slower than typing. That is acceptable. We are not promising a voice mode.

---

## Pre-reveal check (locked)

Before **any** letter is painted, including the last, read the field and test a match.

**Order of a tick**

1. Normalize input (letters only, case-insensitive).
2. If it equals the word → **win, stop**. Do not paint that letter. The board never completes itself on a winning round.
3. Else reveal the next letter.
4. If the board is now complete → **fail immediately**.

This sits next to instant match on keystroke. Typing the word still wins immediately. The tick is a second gate so a timer firing in the same breath as an already-correct field cannot overwrite a win.

This is **not** a grace period. The completed word is never sitting on screen while the player still has time. Either they already had it (win, no last paint) or they did not (reveal and fail).

**What this does not save:** a key that lands *after* step 1 has already decided to reveal. That is still a miss. Do not wait for it.

---

## Word lists

Do not fetch random words from a dictionary API at runtime. Most dictionary APIs look up a word you already have. Random endpoints return obscure words, inflections, and junk. Fairness depends on a graded playable list.

### How to build (dev script, run once, commit the JSON)

1. **Rank** with [`wordfreq`](https://github.com/rspeer/wordfreq) `zipf_frequency(word, "en")`.
   - ~6 very common, ~4 everyday, ~3 uncommon, below ~3 most people will not know it.
2. **Keep** only `^[a-z]{4,6}$`.
3. **Drop** function words (`that`, `with`, `have`, `they`, `from`, …). They dominate the top of any 4-letter frequency list and make “easy” feel like a grammar test.
4. **Drop** profanity/slurs via a blocklist (e.g. [LDNOOBW](https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words), CC BY 4.0).
5. **Floor:** discard Zipf below about **3.4** so the hard end is uncommon, not crossword bait (`cwm`). Knob; inspect the tail by hand.
6. Split into three files, each sorted common → uncommon.

### Where they live

```text
src/data/words/4.json
src/data/words/5.json
src/data/words/6.json
scripts/build-wordlists.py
ATTRIBUTION.md
```

Shape:

```json
[{ "w": "house", "z": 5.41 }, { "w": "flame", "z": 4.62 }]
```

Runtime only needs `w`. Keep `z` so bands can be retuned without rebuilding.

### Licensing

- `wordfreq` code: Apache-2.0
- Frequency data: CC BY-SA 4.0 (wordfreq, SUBTLEX, OpenSubtitles — see their NOTICE)
- LDNOOBW: CC BY 4.0

Keep `ATTRIBUTION.md`. Mark the JSON as derived data. Do not paste Oxford / Merriam-Webster text into the repo. Game source can be a normal license; the generated lists carry the data licenses.

### How a run uses the list

- Shuffle **inside bands**, not the whole file. Walking the sorted file in order is predictable.
- **Six bands** from most common to least. Streak 0–1 uses band 0, 2–3 band 1, then onward. After the last band, stay there.
- No repeats in a single run.
- If a band is exhausted, spill into the next rarer band.

Frequency is not the same as “a player could have known that.” Zipf floor plus a manual pass over the rarest ~50 per length is part of v1, not polish.

---

## Visual

From **joris.wtf**, not from Wordle.

| Token | Value |
|---|---|
| Font | Atkinson Hyperlegible Next, Regular, self-hosted `.woff2` (SIL OFL, Braille Institute). Same as joris.wtf |
| Background | `#070708` |
| Text | `#c8c6c2` |
| Muted | `#a3a19c` |
| Hairline | `#2a2a2e` |
| Focus | `#eceae4` |

**Not Wordle:** no green/yellow states, no five-row grid, no candy tiles, no on-screen A–Z chrome.

**Closer to Phantasm** ([phantasm.joris.wtf](https://phantasm.joris.wtf)): dark field, type appearing out of nothing, lose/win as a quiet overlay. Phantasm’s “done” treatment is the reference for game over: large word, small Play again.

**Utilitarian:** score as a number, length as `4` `5` `6`, one input. Letters as type (e.g. `S····` or dim upcoming glyphs), not a toy board. No sound. No extra motion beyond a letter arriving. Optional light haptic on win/lose if the browser allows it; not required.

---

## Screens

1. **Start** — length choice + Start.
2. **Play** — word, field, score.
3. **Game over** — word, streak, Play again.

Empty/error: if a word list fails to load, say so and offer retry. Lists are bundled, so this should be rare.

No accounts, persistence, definitions, custom voice, mid-run length change, or leaderboard.

---

## Implementation risks

**iOS keyboard** is the highest-risk detail.

- Keyboard opens from the Start tap, not from `onload` focus alone.
- Never blur between words.
- Layout uses `visualViewport` so the puzzle stays above the keyboard.
- Some Android keyboards ignore `autocorrect="off"`. If that shows up in testing, a later custom A–Z pad is the fallback. Not v1.

**Answers are in the client.** Anyone can read the JSON. Fine for v1 with no leaderboard. Do not pretend the word is secret.

**4-letter early rounds are a lottery** after `S _ _ _`. Players will wait-then-burst. That is inherent if the only clue is letters. Do not add themes/categories in v1.

**Immediate fail vs mobile latency.** Pre-reveal catches “already typed.” It does not catch a tap ~80ms after the reveal. That is accepted.

**If late games always die on the last glyph,** the interval is too short or the tail is too obscure. Change the 1.8s knob or the Zipf floor. Do not reintroduce a speed curve or a post-reveal grace in v1.

---

## Out of scope for v1

- Timer that speeds up per win
- Grace period after the full word is visible
- Next.js / Vercel / OpenNext
- shadcn or any UI kit
- Custom speech recognition
- Live dictionary API for the random word
- Definitions
- Sound
- Persistence / high scores
- Auth
- Mixing 4/5/6 in one run
- Last letter left blank forever (would need a second fuse; rejected in favor of immediate fail + pre-reveal)

---

## Playtest knobs (not product features)

| Knob | First value |
|---|---|
| Reveal interval | 1.8s |
| Zipf floor | ~3.4 |
| Band count | 6 |
| Streaks per band | 2 |

If 1.8s feels wrong, change the number. Do not add a curve.

---

## Suggested first build slice

1. Scaffold Vite + Svelte 5 + TS. Atkinson, dark tokens, Wrangler static assets config.
2. Start screen → focused field + dummy word → instant match / fail overlay.
3. Reveal timer + locked prefix + type-ahead + **pre-reveal check**.
4. Word-list script + three JSON files + banded selection, no repeats.
5. iOS keyboard pass: Start tap, no blur, visual viewport.
6. Deploy to Workers.

Done for v1 means: a phone can start, type at thinking speed, win on instant match, lose when the last letter paints, and play again. Streak is on screen and gone when the tab closes.
