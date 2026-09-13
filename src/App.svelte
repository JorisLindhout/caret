<script lang="ts">
	import { flushSync, onMount } from 'svelte';
	import { on } from 'svelte/events';
	import { Game, REVEAL_MS, STARTING_LIVES } from './lib/game.svelte.ts';
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
	const levels: { n: WordLength; label: string }[] = [
		{ n: 6, label: 'Easy' },
		{ n: 5, label: 'Normal' },
		{ n: 4, label: 'Hard' }
	];

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

{#snippet iconPlay()}
	<svg class="icon" viewBox="0 0 16 16" aria-hidden="true">
		<path d="M5 3.2v9.6L13 8z" fill="currentColor" />
	</svg>
{/snippet}

{#snippet iconRetry()}
	<svg class="icon" viewBox="0 0 16 16" aria-hidden="true">
		<path
			d="M13.4 8A5.4 5.4 0 1 1 11.1 3.4"
			fill="none"
			stroke="currentColor"
			stroke-width="1.35"
			stroke-linecap="round"
		/>
		<path
			d="M13.65 1.55v3.35h-3.35"
			fill="none"
			stroke="currentColor"
			stroke-width="1.35"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
{/snippet}

{#snippet dots(count: number)}
	<span class="dots" aria-hidden="true">
		{#each { length: count }}
			<span class="dot"></span>
		{/each}
	</span>
{/snippet}

<div class="shell">
	{#if game.screen === 'start'}
		<div class="screen start">
			<h1 class="title">Caret</h1>
			<p class="lede">Guess the word before it finishes itself.</p>
			<div class="levels" role="group" aria-label="Difficulty">
				{#each levels as level (level.n)}
					<button
						type="button"
						class={['level', game.length === level.n && 'on']}
						aria-pressed={game.length === level.n}
						onclick={() => game.selectLength(level.n)}
					>
						{@render dots(level.n)}
						<span class="level-label">{level.label}</span>
					</button>
				{/each}
			</div>
			<button type="button" class="go" onclick={onStart}>
				{@render iconPlay()}
				Start
			</button>
		</div>
	{:else if game.screen === 'error'}
		<div class="screen start">
			<p class="lede">{game.loadError}</p>
			<button type="button" class="go" onclick={onStart}>
				{@render iconRetry()}
				Retry
			</button>
		</div>
	{:else if game.screen === 'over'}
		<div class="screen over">
			<h1 class="over-title">Game over</h1>
			<p class="score big">Score: {game.score}</p>
			<button type="button" class="go icon-only" aria-label="Retry" onclick={game.retry}>
				{@render iconRetry()}
			</button>
		</div>
	{:else if game.screen === 'play' || game.screen === 'paused'}
		<div class="play">
			<div class="hud">
				<p class="score">
					<span class="sr">Score</span>
					<span>{game.score}</span>
				</p>
				<p class="lives" role="status">
					<span class="sr">{game.lives} of {STARTING_LIVES} lives</span>
					{#each { length: STARTING_LIVES }, i}
						<span class={['life', i < game.lives && 'on']} aria-hidden="true"></span>
					{/each}
				</p>
			</div>
			<div
				class={['board', game.held && 'hit']}
				style:--reveal-ms="{REVEAL_MS}ms"
				aria-hidden="true"
			>
				{#each board as ch, i (game.word + i)}
					{#if i === game.revealed && !game.held}
						{#key game.beat}
							<span class="glyph await">·</span>
						{/key}
					{:else}
						<span class={['glyph', i < game.revealed && 'on']}>
							{i < game.revealed ? ch.toUpperCase() : '·'}
						</span>
					{/if}
				{/each}
			</div>
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
				aria-label="Guess the {game.length}-letter word. Score {game.score}. {game.lives} of {STARTING_LIVES} lives."
				oninput={(event) => game.handleInput(event.currentTarget.value)}
				onbeforeinput={(event) => game.handleBeforeInput(event)}
				onblur={onFieldBlur}
				onkeydown={(event) => {
					if (event.key === 'Enter') event.preventDefault();
				}}
			/>
			{#if game.screen === 'paused'}
				<button type="button" class="resume" onclick={onResume}>
					{@render iconPlay()}
					Continue
				</button>
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

	.screen,
	.play {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-height: 0;
	}

	.start,
	.over {
		justify-content: center;
		gap: 1.75rem;
	}

	.title,
	.lede,
	.score,
	.over-title {
		margin: 0;
	}

	.title {
		color: var(--focus);
		font-size: 1.5rem;
		font-weight: 400;
		letter-spacing: 0.08em;
	}

	.lede {
		color: var(--muted);
		max-width: 16rem;
	}

	.over-title {
		color: var(--focus);
		font-size: 1.5rem;
		font-weight: 400;
		letter-spacing: 0.06em;
	}

	.levels {
		display: flex;
		gap: 1.5rem;
	}

	.level,
	.go,
	.resume {
		appearance: none;
		background: none;
		border: 0;
		padding: 0;
		margin: 0;
		color: var(--muted);
		font: inherit;
		letter-spacing: 0.04em;
		cursor: pointer;
	}

	.level {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 0.45rem;
	}

	.level.on,
	.go,
	.resume {
		color: var(--focus);
	}

	.level-label {
		font-size: 0.85rem;
	}

	.dots {
		display: flex;
		gap: 0.22rem;
		height: 0.55rem;
		align-items: center;
	}

	.dot {
		width: 0.32rem;
		height: 0.32rem;
		border-radius: 50%;
		background: currentColor;
	}

	.go,
	.resume {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		align-self: flex-start;
	}

	.go.icon-only {
		padding: 0.2rem;
	}

	.go.icon-only .icon {
		width: 1.2rem;
		height: 1.2rem;
	}

	.icon {
		width: 1rem;
		height: 1rem;
		flex: 0 0 auto;
		display: block;
	}

	.play {
		position: relative;
	}

	.hud {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	.score {
		color: var(--fg);
	}

	.lives {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		margin: 0;
	}

	.life {
		box-sizing: border-box;
		width: 0.5rem;
		height: 0.5rem;
		border-radius: 50%;
		border: 1.25px solid var(--muted);
		background: transparent;
	}

	.life.on {
		border-color: var(--focus);
		background: var(--focus);
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

	.glyph.await {
		animation: warn-dot var(--reveal-ms, 1800ms) linear forwards;
	}

	@keyframes warn-dot {
		0%,
		42% {
			opacity: 1;
		}
		50% {
			opacity: 0.12;
		}
		57% {
			opacity: 1;
		}
		65% {
			opacity: 0.12;
		}
		72% {
			opacity: 1;
		}
		75% {
			opacity: 0.12;
		}
		78% {
			opacity: 1;
		}
		81% {
			opacity: 0.12;
		}
		84% {
			opacity: 1;
		}
		86% {
			opacity: 0.12;
		}
		88% {
			opacity: 1;
		}
		90% {
			opacity: 0.12;
		}
		92% {
			opacity: 1;
		}
		93.5% {
			opacity: 0.12;
		}
		95% {
			opacity: 1;
		}
		96.5% {
			opacity: 0.12;
		}
		98% {
			opacity: 1;
		}
		99% {
			opacity: 0.12;
		}
		100% {
			opacity: 1;
		}
	}

	.board.hit {
		animation: hit 0.4s ease-in-out;
	}

	@keyframes hit {
		0%,
		100% {
			opacity: 1;
		}
		45% {
			opacity: 0.12;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.board.hit,
		.glyph.await {
			animation: none;
		}
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

	.resume {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
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
