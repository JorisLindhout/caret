export function normalize(raw: string): string {
  return raw.toLowerCase().replace(/[^a-z]/g, '')
}

export function lockedPrefix(word: string, revealed: number): string {
  return word.slice(0, revealed)
}

/** Sanitize paste/keystrokes and keep the locked revealed prefix. */
export function applyInput(raw: string, word: string, revealed: number): string {
  const n = word.length
  const locked = lockedPrefix(word, revealed)
  const typed = normalize(raw).slice(0, n)

  if (typed.startsWith(locked)) {
    return typed
  }

  const leftover = typed.length >= revealed ? typed.slice(revealed) : ''
  return (locked + leftover).slice(0, n)
}

/** If a new reveal contradicts type-ahead, snap back to the prefix. */
export function snapAfterReveal(guess: string, word: string, revealed: number): string {
  const locked = lockedPrefix(word, revealed)
  const g = normalize(guess)
  if (g.startsWith(locked)) {
    return g.slice(0, word.length)
  }
  return locked
}

export function isMatch(guess: string, word: string): boolean {
  return normalize(guess) === word
}

export function displayGuess(guess: string): string {
  return normalize(guess).toUpperCase()
}
