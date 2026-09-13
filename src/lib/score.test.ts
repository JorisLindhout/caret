import { describe, expect, it } from 'vitest'
import { pointsForGuess } from './score'

describe('pointsForGuess', () => {
  it('awards leftover letters on an immediate easy guess', () => {
    expect(pointsForGuess(4, 1)).toBe(3)
  })

  it('awards one point when three letters are already visible', () => {
    expect(pointsForGuess(4, 3)).toBe(1)
    expect(pointsForGuess(5, 3)).toBe(2)
  })

  it('awards nothing once the board is complete', () => {
    expect(pointsForGuess(5, 5)).toBe(0)
  })
})
