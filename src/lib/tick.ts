import { isMatch, snapAfterReveal } from './input'

export type TickResult =
  | { kind: 'win' }
  | { kind: 'reveal'; revealed: number; guess: string }
  | { kind: 'lose'; guess: string }

/**
 * Order of a tick:
 * 1. If the field already matches, win and do not paint.
 * 2. Else reveal the next letter (snapping type-ahead if it contradicts).
 * 3. If the board is now complete, fail immediately.
 */
export function tick(guess: string, word: string, revealed: number): TickResult {
  if (isMatch(guess, word)) {
    return { kind: 'win' }
  }

  const next = Math.min(word.length, revealed + 1)
  const snapped = snapAfterReveal(guess, word, next)

  if (next >= word.length) {
    return { kind: 'lose', guess: snapped }
  }

  return { kind: 'reveal', revealed: next, guess: snapped }
}
