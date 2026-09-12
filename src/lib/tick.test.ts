import { describe, expect, it } from 'vitest'
import { tick } from './tick'

describe('tick', () => {
  it('wins before painting when the field already matches', () => {
    expect(tick('house', 'house', 3)).toEqual({ kind: 'win' })
  })

  it('reveals the next letter when there is no match', () => {
    expect(tick('h', 'house', 1)).toEqual({
      kind: 'reveal',
      revealed: 2,
      guess: 'ho',
    })
  })

  it('snaps contradicting type-ahead on reveal', () => {
    expect(tick('hate', 'house', 1)).toEqual({
      kind: 'reveal',
      revealed: 2,
      guess: 'ho',
    })
  })

  it('fails immediately when the last letter is painted', () => {
    expect(tick('housx', 'house', 4)).toEqual({
      kind: 'lose',
      guess: 'house',
    })
  })
})
