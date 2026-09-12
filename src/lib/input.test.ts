import { describe, expect, it } from 'vitest'
import { applyInput, isMatch, normalize, snapAfterReveal } from './input'

describe('normalize', () => {
  it('strips case, spaces, and punctuation', () => {
    expect(normalize(' House! ')).toBe('house')
    expect(normalize('FLAME')).toBe('flame')
  })
})

describe('applyInput', () => {
  it('locks the revealed prefix', () => {
    expect(applyInput('', 'house', 1)).toBe('h')
    expect(applyInput('x', 'house', 1)).toBe('h')
    expect(applyInput('hate', 'house', 1)).toBe('hate')
  })

  it('keeps type-ahead past the prefix', () => {
    expect(applyInput('hous', 'house', 1)).toBe('hous')
    expect(applyInput('house', 'house', 2)).toBe('house')
  })

  it('cannot delete the locked prefix', () => {
    expect(applyInput('o', 'house', 2)).toBe('ho')
    expect(applyInput('', 'house', 3)).toBe('hou')
  })

  it('sanitizes paste', () => {
    expect(applyInput('  Ho-use!! ', 'house', 1)).toBe('house')
    expect(applyInput('abcdefgh', 'house', 1)).toBe('hbcde')
  })
})

describe('snapAfterReveal', () => {
  it('keeps matching type-ahead', () => {
    expect(snapAfterReveal('hous', 'house', 2)).toBe('hous')
  })

  it('snaps when the new letter contradicts type-ahead', () => {
    expect(snapAfterReveal('hate', 'house', 2)).toBe('ho')
  })
})

describe('isMatch', () => {
  it('matches case-insensitively after sanitizing', () => {
    expect(isMatch('HOUSE', 'house')).toBe(true)
    expect(isMatch('ho use', 'house')).toBe(true)
    expect(isMatch('hous', 'house')).toBe(false)
  })
})
