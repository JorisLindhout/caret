/** Points for a correct guess: one per letter still hidden. */
export function pointsForGuess(wordLength: number, revealed: number): number {
  return Math.max(0, wordLength - revealed)
}
