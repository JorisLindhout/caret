import { haptic } from './haptic'
import { applyInput, isMatch } from './input'
import { tick } from './tick'
import type { Screen, WordEntry, WordLength } from './types'
import { WordPicker } from './words'

export const REVEAL_MS = 1800

export class Game {
  screen = $state<Screen>('start')
  length = $state<WordLength>(5)
  score = $state(0)
  word = $state('')
  revealed = $state(1)
  guess = $state('')
  loadError = $state('')

  private picker: WordPicker | null = null
  private timer: ReturnType<typeof setInterval> | null = null
  private lists: Record<WordLength, WordEntry[]>

  constructor(lists: Record<WordLength, WordEntry[]>) {
    this.lists = lists
  }

  selectLength = (n: WordLength) => {
    this.length = n
    if (this.screen === 'over' || this.screen === 'play' || this.screen === 'paused') {
      this.stopTimer()
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
      this.loadError = ''
      this.screen = 'play'
      this.dealWord()
    } catch (error) {
      this.loadError = error instanceof Error ? error.message : 'Word list failed to load.'
      this.screen = 'error'
    }
  }

  handleInput = (raw: string) => {
    if (this.screen !== 'play') return
    this.guess = applyInput(raw, this.word, this.revealed)
    if (isMatch(this.guess, this.word)) {
      this.win()
    }
  }

  handleBeforeInput = (event: InputEvent) => {
    if (this.screen !== 'play') return
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
    if (this.screen === 'play') {
      this.stopTimer()
      this.screen = 'paused'
    }
  }

  resume = () => {
    if (this.screen !== 'paused') return
    this.screen = 'play'
    this.startTimer()
  }

  playAgain = () => {
    this.start()
  }

  retry = () => {
    this.start()
  }

  destroy = () => {
    this.stopTimer()
  }

  private dealWord() {
    const next = this.picker?.next(this.score)
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
    this.score += 1
    haptic(12)
    this.dealWord()
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
    this.screen = 'over'
    haptic(28)
  }

  private startTimer() {
    this.stopTimer()
    this.timer = setInterval(() => this.onTick(), REVEAL_MS)
  }

  private stopTimer() {
    if (this.timer !== null) {
      clearInterval(this.timer)
      this.timer = null
    }
  }
}
