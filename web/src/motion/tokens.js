/**
 * Motion tokens — "Propagation".
 * The vocabulary comes from what the site explains: a neuron integrates
 * below threshold and then fires; a spike travels down an axon; after
 * firing comes a refractory pause; the katamari accumulates what it touches.
 */

/** The ease of the slow, sub-threshold climb. Same curve as --ease-out. */
export const MEMBRANE_EASE = [0.22, 1, 0.36, 1];

export const SPRING = {
  /** Firing: fast, tight, a hint of overshoot. */
  spike: { type: 'spring', stiffness: 520, damping: 32, mass: 0.9 },
  /** Settling into place. */
  settle: { type: 'spring', stiffness: 140, damping: 22 },
  /** Scroll smoothing for progress lines (rail, axon). */
  scroll: { stiffness: 120, damping: 30, restDelta: 0.0005 },
  /** Cursor depth. Soft, so the scene drifts rather than tracks. */
  pointer: { stiffness: 60, damping: 18, mass: 0.6 },
};

export const DURATION = {
  membrane: 0.7,
  quick: 0.22,
  fade: 0.2,
};

/** Stagger rhythm: fixed interval, capped cascade. */
export const REFRACTORY = 0.06;
export const MAX_CASCADE = 6;

/** Delay for item i in a cascade, capped so long lists arrive together. */
export const cascade = (i, base = 0) => base + Math.min(i, MAX_CASCADE) * REFRACTORY;

/** Parallax depth layers (px of travel per layer) and the mobile damping. */
export const DEPTH = { near: 90, mid: 45, far: 24 };
export const MOBILE_FACTOR = 0.5;

/** Viewport trigger for one-shot reveals. Low amount so fast jumps never strand content. */
export const IN_VIEW = { once: true, amount: 0.15, margin: '0px 0px -8% 0px' };
