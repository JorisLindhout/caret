# Caret

A mobile-first word game: guess the word before it autocompletes.

A short English word starts with one letter. The rest fill in left to right
on a fixed timer. Type the word in one field. Match it and you win the
round instantly. If the board finishes the word, the run ends. Score is the
streak until the first miss. Nothing is saved.

Full spec: [PLAN.md](./PLAN.md). Data licenses: [ATTRIBUTION.md](./ATTRIBUTION.md).

## Local

```bash
npm install
npm test
npm run dev
```

Dev server: `http://localhost:4731`.

Rebuild playable lists (dev only; JSON is already committed):

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
npm run words
```

## Ship

```bash
npm run build
npx wrangler deploy
```

Static Vite bundle on Cloudflare Workers assets. No server, no API routes.
