<script lang="ts">
	import { flushSync, onMount } from 'svelte';
	import { on } from 'svelte/events';
	import { Game } from './lib/game.svelte.ts';
	import { displayGuess } from './lib/input';
	import type { WordLength } from './lib/types';
	import words4 from './data/words/4.json';
	import words5 from './data/words/5.json';
	import words6 from './data/words/6.json';

	const game = new Game({
		4: words4,
		5: words5,
		6: words6
	});

	if (import.meta.env.DEV) {
		(window as Window & { __caret?: Game }).__caret = game;
	}

	let field = $state<HTMLInputElement | null>(null);
	const lengths: WordLength[] = [4, 5, 6];

	function syncViewport() {
		const vv = window.visualViewport;
		const height = vv?.height ?? window.innerHeight;
		document.documentElement.style.setProperty('--vvh', `${height}px`);
		document.documentElement.style.setProperty('--vv-offset', `${vv?.offsetTop ?? 0}px`);
	}

	onMount(() => {
		syncViewport();
		const vv = window.visualViewport;
		const offResize = vv ? on(vv, 'resize', syncViewport) : () => {};
		const offScroll = vv ? on(vv, 'scroll', syncViewport) : () => {};
		return () => {
			offResize();
			offScroll();
			game.destroy();
		};
	});

	function focusField() {
		field?.focus({ preventScroll: true });
	}

	function onStart() {
		flushSync(() => {
			game.start();
		});
		focusField();
	}

	function onResume() {
		flushSync(() => {
			game.resume();
		});
		focusField();
	}

	function onPlayAgain() {
		flushSync(() => {
			game.playAgain();
		});
		focusField();
	}

	function onVisibility() {
		if (document.hidden) {
			game.hide();
		}
	}

	function keepPlayFocus() {
		if (game.screen === 'play') {
			focusField();
		}
	}

	function onFieldBlur() {
		if (game.screen === 'play') {
			focusField();
		}
	}

	const board = $derived(game.word.split(''));
</script>

<svelte:head>
	<title>Caret</title>
</svelte:head>

<svelte:window onclick={keepPlayFocus} onresize={syncViewport} />
<svelte:document onvisibilitychange={onVisibility} />

<div class="shell">
	{#if game.screen === 'start'}
		<header class="top">
			<p class="mark">Caret</p>
		</header>
		<div class="center">
			<p class="lede">Guess the word before it finishes itself.</p>
			<div class="lengths" role="group" aria-label="Word length">
				{#each lengths as n (n)}
					<button
						type="button"
						class={['len', game.length === n && 'on']}
						aria-pressed={game.length === n}
						onclick={() => game.selectLength(n)}
					>
						{n}
					</button>
				{/each}
			</div>
			<button type="button" class="go" onclick={onStart}>Start</button>
		</div>
	{:else if game.screen === 'error'}
		<div class="center">
			<p class="lede">{game.loadError}</p>
			<button type="button" class="go" onclick={game.retry}>Retry</button>
		</div>
	{:else if game.screen === 'over'}
		<div class="over">
			<p class="over-word">{game.word.toUpperCase()}</p>
			<p class="score big">{game.score}</p>
			<button type="button" class="go" onclick={onPlayAgain}>Play again</button>
			<div class="lengths quiet" role="group" aria-label="Change length">
				{#each lengths as n (n)}
					<button
						type="button"
						class={['len', game.length === n && 'on']}
						aria-pressed={game.length === n}
						onclick={() => game.selectLength(n)}
					>
						{n}
					</button>
				{/each}
			</div>
		</div>
	{:else}
		<div class="play">
			<p class="score">{game.score}</p>
			<div class="board" aria-hidden="true">
				{#each board as ch, i (game.word + i)}
					<span class={['glyph', i < game.revealed && 'on']}>
						{i < game.revealed ? ch.toUpperCase() : '·'}
					</span>
				{/each}
			</div>
			<label class="sr" for="guess">Guess the word</label>
			<input
				id="guess"
				bind:this={field}
				class="guess"
				value={displayGuess(game.guess)}
				maxlength={game.length}
				autocorrect="off"
				autocomplete="off"
				spellcheck="false"
				autocapitalize="characters"
				inputmode="text"
				enterkeyhint="done"
				inert={game.screen === 'paused'}
				aria-label="Guess the {game.length}-letter word. Score {game.score}."
				oninput={(event) => game.handleInput(event.currentTarget.value)}
				onbeforeinput={(event) => game.handleBeforeInput(event)}
				onblur={onFieldBlur}
				onkeydown={(event) => {
					if (event.key === 'Enter') event.preventDefault();
				}}
			/>
			{#if game.screen === 'paused'}
				<button type="button" class="resume" onclick={onResume}>Tap to continue</button>
			{/if}
		</div>
	{/if}
</div>

<style>
	.shell {
		box-sizing: border-box;
		min-height: var(--vvh, 100dvh);
		height: var(--vvh, 100dvh);
		transform: translateY(var(--vv-offset, 0px));
		padding: 1.25rem;
		padding-top: max(1.25rem, env(safe-area-inset-top));
		padding-bottom: max(1.25rem, env(safe-area-inset-bottom));
		display: flex;
		flex-direction: column;
	}

	.top {
		min-height: 1.5rem;
	}

	.mark,
	.lede,
	.score {
		margin: 0;
	}

	.mark {
		color: var(--muted);
		letter-spacing: 0.08em;
	}

	.lede {
		color: var(--muted);
		max-width: 16rem;
	}

	.center,
	.over {
		flex: 1;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 1.75rem;
	}

	.lengths {
		display: flex;
		gap: 1.25rem;
	}

	.lengths.quiet {
		margin-top: 0.25rem;
	}

	.len,
	.go,
	.resume {
		appearance: none;
		background: none;
		border: 0;
		padding: 0;
		margin: 0;
		color: var(--muted);
		font: inherit;
		letter-spacing: 0.06em;
		cursor: pointer;
	}

	.len.on,
	.go,
	.resume {
		color: var(--focus);
	}

	.go,
	.resume {
		align-self: flex-start;
	}

	.play {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-height: 0;
		position: relative;
	}

	.score {
		color: var(--fg);
	}

	.score.big {
		color: var(--muted);
	}

	.board {
		margin-top: 16vh;
		font-size: clamp(2.25rem, 12vw, 3.75rem);
		letter-spacing: 0.22em;
		line-height: 1;
	}

	.glyph {
		color: var(--muted);
	}

	.glyph.on {
		color: var(--focus);
	}

	.guess {
		margin-top: 1.75rem;
		width: 100%;
		border: 0;
		border-bottom: 1px solid var(--hairline);
		border-radius: 0;
		background: transparent;
		color: var(--focus);
		font: inherit;
		font-size: 1.15rem;
		letter-spacing: 0.2em;
		text-transform: uppercase;
		caret-color: var(--focus);
		outline: none;
		padding: 0.45rem 0;
	}

	.guess:focus {
		border-bottom-color: var(--focus);
	}

	.over-word {
		margin: 0;
		color: var(--focus);
		font-size: clamp(2.75rem, 14vw, 4.75rem);
		letter-spacing: 0.14em;
		line-height: 1;
		text-transform: uppercase;
	}

	.resume {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--bg);
		letter-spacing: 0.04em;
	}

	.sr {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}
</style>
