import { describe, expect, it } from 'vitest'
import { bandForScore, splitBands, WordPicker } from './words'

const list = Array.from({ length: 12 }, (_, i) => ({
  w: `w${String(i).padStart(2, '0')}`,
  z: 6 - i * 0.2,
}))

describe('bandForScore', () => {
  it('moves a band every two wins and stays on the last', () => {
    expect(bandForScore(0)).toBe(0)
    expect(bandForScore(1)).toBe(0)
    expect(bandForScore(2)).toBe(1)
    expect(bandForScore(11)).toBe(5)
    expect(bandForScore(99)).toBe(5)
  })
})

describe('splitBands', () => {
  it('keeps common words in earlier bands', () => {
    const bands = splitBands(list)
    expect(bands).toHaveLength(6)
    expect(bands[0]?.[0]?.w).toBe('w00')
    expect(bands.at(-1)?.at(-1)?.w).toBe('w11')
  })
})

describe('WordPicker', () => {
  it('does not repeat a word in a run', () => {
    let i = 0
    const rng = () => {
      i += 0.01
      return i % 1
    }
    const picker = new WordPicker(list, rng)
    const seen = new Set<string>()

    for (let score = 0; score < 12; score++) {
      const word = picker.next(score)
      expect(word).toBeTruthy()
      expect(seen.has(word!)).toBe(false)
      seen.add(word!)
    }

    expect(picker.next(12)).toBeNull()
  })

  it('spills into the next rarer band when empty', () => {
    const thin = [
      { w: 'aaaa', z: 6 },
      { w: 'bbbb', z: 5 },
      { w: 'cccc', z: 4 },
      { w: 'dddd', z: 3.5 },
      { w: 'eeee', z: 3.4 },
      { w: 'ffff', z: 3.4 },
    ]
    const picker = new WordPicker(thin, () => 0)
    const first = picker.next(0)
    const second = picker.next(0)
    expect(first).toBe('aaaa')
    expect(second).toBe('bbbb')
  })
})
