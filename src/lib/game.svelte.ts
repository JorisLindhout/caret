import { haptic } from './haptic'
import { applyInput, isMatch } from './input'
import { pointsForGuess } from './score'
import { tick } from './tick'
import type { Screen, WordEntry, WordLength } from './types'
import { WordPicker } from './words'

export const REVEAL_MS = 1800
export const HOLD_MS = 450
export const STARTING_LIVES = 3

type AfterHold = 'next' | 'over'

export class Game {
  screen = $state<Screen>('start')
  length = $state<WordLength>(5)
  score = $state(0)
  lives = $state(STARTING_LIVES)
  word = $state('')
  revealed = $state(1)
  guess = $state('')
  loadError = $state('')
  held = $state(false)
  /** Bumps when a reveal interval starts so the next-dot warn remounts. */
  beat = $state(0)

  private picker: WordPicker | null = null
  private timer: ReturnType<typeof setInterval> | null = null
  private holdPause: ReturnType<typeof setTimeout> | null = null
  private afterHold: AfterHold | null = null
  private pendingAdvance = false
  private wins = 0
  private lists: Record<WordLength, WordEntry[]>

  constructor(lists: Record<WordLength, WordEntry[]>) {
    this.lists = lists
  }

  selectLength = (n: WordLength) => {
    this.length = n
    if (this.screen === 'over' || this.screen === 'play' || this.screen === 'paused') {
      this.resetRun()
      this.screen = 'start'
    }
  }

  start = () => {
    try {
      const list = this.lists[this.length]
      if (!list?.length) {
        throw new Error('Word list failed to load.')
      }
      this.picker = new WordPicker(list)
      this.score = 0
      this.wins = 0
      this.lives = STARTING_LIVES
      this.loadError = ''
      this.resetHold()
      this.screen = 'play'
      this.dealWord()
    } catch (error) {
      this.loadError = error instanceof Error ? error.message : 'Word list failed to load.'
      this.screen = 'error'
    }
  }

  handleInput = (raw: string) => {
    if (this.screen !== 'play' || this.held) return
    this.guess = applyInput(raw, this.word, this.revealed)
    if (isMatch(this.guess, this.word)) {
      this.win()
    }
  }

  handleBeforeInput = (event: InputEvent) => {
    if (this.screen !== 'play' || this.held) return
    if (
      event.inputType !== 'deleteContentBackward' &&
      event.inputType !== 'deleteContentForward' &&
      event.inputType !== 'deleteByCut'
    ) {
      return
    }

    const input = event.target
    if (!(input instanceof HTMLInputElement)) return

    const start = input.selectionStart ?? 0
    const end = input.selectionEnd ?? 0
    const locked = this.revealed

    if (start < locked || (start === end && start <= locked && event.inputType === 'deleteContentBackward')) {
      event.preventDefault()
      this.guess = applyInput(input.value, this.word, this.revealed)
    }
  }

  hide = () => {
    if (this.screen !== 'play') return
    this.stopTimer()
    if (this.held || this.holdPause !== null) {
      this.clearHoldPause()
      this.pendingAdvance = true
    }
    this.screen = 'paused'
  }

  resume = () => {
    if (this.screen !== 'paused') return
    this.screen = 'play'
    if (this.pendingAdvance && this.afterHold) {
      this.pendingAdvance = false
      this.finishHold(this.afterHold)
      return
    }
    this.startTimer()
  }

  toStart = () => {
    this.resetRun()
    this.screen = 'start'
  }

  retry = () => {
    this.toStart()
  }

  destroy = () => {
    this.stopTimer()
    this.clearHoldPause()
  }

  private resetRun() {
    this.stopTimer()
    this.resetHold()
  }

  private resetHold() {
    this.clearHoldPause()
    this.held = false
    this.afterHold = null
    this.pendingAdvance = false
  }

  private dealWord() {
    const next = this.picker?.next(this.wins)
    if (!next) {
      this.stopTimer()
      this.screen = 'over'
      return
    }

    this.word = next
    this.revealed = 1
    this.guess = next[0] ?? ''
    this.startTimer()
  }

  private win() {
    this.stopTimer()
    this.score += pointsForGuess(this.word.length, this.revealed)
    this.wins += 1
    this.revealed = this.word.length
    this.guess = this.word
    haptic(12)
    this.holdThen('next')
  }

  private onTick() {
    const result = tick(this.guess, this.word, this.revealed)
    if (result.kind === 'win') {
      this.win()
      return
    }

    this.guess = result.guess
    if (result.kind === 'reveal') {
      this.revealed = result.revealed
      if (isMatch(this.guess, this.word)) {
        this.win()
      }
      return
    }

    this.revealed = this.word.length
    this.lose()
  }

  private lose() {
    this.stopTimer()
    this.guess = this.word
    this.lives = Math.max(0, this.lives - 1)
    haptic(28)
    this.holdThen(this.lives > 0 ? 'next' : 'over')
  }

  private holdThen(next: AfterHold) {
    this.clearHoldPause()
    this.afterHold = next
    this.held = true
    this.holdPause = setTimeout(() => {
      this.holdPause = null
      this.finishHold(next)
    }, HOLD_MS)
  }

  private finishHold(next: AfterHold) {
    this.held = false
    this.afterHold = null
    this.pendingAdvance = false
    if (next === 'over') {
      this.screen = 'over'
      return
    }
    this.dealWord()
  }

  private startTimer() {
    this.stopTimer()
    this.beat += 1
    this.timer = setInterval(() => this.onTick(), REVEAL_MS)
  }

  private stopTimer() {
    if (this.timer !== null) {
      clearInterval(this.timer)
      this.timer = null
    }
  }

  private clearHoldPause() {
    if (this.holdPause !== null) {
      clearTimeout(this.holdPause)
      this.holdPause = null
    }
  }
}
