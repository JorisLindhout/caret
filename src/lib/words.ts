import type { WordEntry } from './types'

export const BAND_COUNT = 6
export const STREAKS_PER_BAND = 2

export function bandForScore(score: number): number {
  return Math.min(BAND_COUNT - 1, Math.floor(score / STREAKS_PER_BAND))
}

export function splitBands(list: WordEntry[]): WordEntry[][] {
  const n = list.length
  const bands: WordEntry[][] = []
  const base = Math.floor(n / BAND_COUNT)
  let extra = n % BAND_COUNT
  let i = 0

  for (let b = 0; b < BAND_COUNT; b++) {
    const take = base + (extra > 0 ? 1 : 0)
    if (extra > 0) extra -= 1
    bands.push(list.slice(i, i + take))
    i += take
  }

  return bands
}

export function shuffle<T>(arr: readonly T[], rng: () => number = Math.random): T[] {
  const a = arr.slice()
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    const current = a[i]
    const swap = a[j]
    if (current === undefined || swap === undefined) continue
    a[i] = swap
    a[j] = current
  }
  return a
}

export class WordPicker {
  private queues: string[][]
  private used = new Set<string>()

  constructor(list: WordEntry[], rng: () => number = Math.random) {
    this.queues = splitBands(list).map((band) => shuffle(
      band.map((entry) => entry.w),
      rng,
    ))
  }

  next(score: number): string | null {
    let band = bandForScore(score)

    while (band < this.queues.length) {
      const queue = this.queues[band]
      if (!queue) break

      while (queue.length) {
        const word = queue.shift()
        if (word && !this.used.has(word)) {
          this.used.add(word)
          return word
        }
      }

      band += 1
    }

    return null
  }
}
