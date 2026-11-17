/**
 * Minimal pub/sub for cross-component signals that should not go through
 * React state (e.g. a spike drawn on a canvas that a table row reacts to).
 * Dependency-free so test-imported modules stay free of the motion package.
 */
const channels = new Map();

export function on(name, fn) {
  if (!channels.has(name)) channels.set(name, new Set());
  channels.get(name).add(fn);
  return () => channels.get(name)?.delete(fn);
}

export function emit(name, payload) {
  channels.get(name)?.forEach((fn) => fn(payload));
}
