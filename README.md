# Caret

Guess the word before it finishes itself.

[caret.joris.wtf](https://caret.joris.wtf) — Vite + Svelte 5 on Cloudflare Workers. Word lists and typeface: [ATTRIBUTION.md](./ATTRIBUTION.md).

## Play

A short English word starts with one letter. The rest fill in left to right every 1.8s. Type the word in one field. An exact match wins the round instantly, even if the next letter was about to paint.

- **Length** is 4, 5, or 6, chosen before the run. It never mixes.
- **Score** is one point per letter still hidden when you match.
- **Lives** are three. The board finishing the word costs one. Zero is game over; retry goes back to start.
- Words get rarer as you win. Nothing is saved.

The field stays focused between words so the phone keyboard does not drop. Hide the tab and the timer pauses; tap Continue to resume.

## Local

```bash
npm install
npm test
npm run dev
```

Dev server: `http://localhost:4731`.

Playable lists are already committed. Rebuild them (dev only). First run
downloads SSA given names and WordNet into `scripts/.cache/`. Names, places,
and calendar words (months, weekdays, holidays) are dropped unless they also
have a normal dictionary sense, the same split Wordle uses for CHINA vs APRIL.

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
npm run words
```

## Ship

```bash
npm run deploy
```

Static Vite bundle on Cloudflare Workers assets. No server, no API routes. Custom domain: `caret.joris.wtf`.
