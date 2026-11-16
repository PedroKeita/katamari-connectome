/**
 * Shared lifecycle for the WebGL figures: render only while the canvas is
 * on screen and the tab is visible; expose pointer-based drag rotation that
 * works for mouse, pen and touch, and cleans up every listener.
 */

export function createRenderGate(el, { onVisible, rootMargin = '100px' } = {}) {
  let inView = false;
  let firstSeen = false;
  const pageVisible = () => typeof document === 'undefined' || !document.hidden;

  const io = 'IntersectionObserver' in window
    ? new IntersectionObserver(([entry]) => {
        inView = entry.isIntersecting;
        if (inView && !firstSeen) {
          firstSeen = true;
          onVisible?.();
        }
      }, { rootMargin })
    : null;

  if (io) io.observe(el);
  else { inView = true; firstSeen = true; onVisible?.(); }

  return {
    get active() { return inView && pageVisible(); },
    dispose() { io?.disconnect(); },
  };
}

/**
 * Pointer-drag rotation. Returns { state, dispose }; state.x / state.y are
 * accumulated rotations, state.dragging is true while a pointer is held.
 */
export function createDragRotate(el, { sx = 0.01, sy = 0.006, clampX = 1.2 } = {}) {
  const state = { x: 0, y: 0, dragging: false };
  let lx = 0;
  let ly = 0;
  let id = null;

  const down = (e) => {
    id = e.pointerId;
    state.dragging = true;
    lx = e.clientX;
    ly = e.clientY;
    el.setPointerCapture?.(id);
  };
  const move = (e) => {
    if (!state.dragging || e.pointerId !== id) return;
    state.y += (e.clientX - lx) * sx;
    state.x = Math.max(-clampX, Math.min(clampX, state.x + (e.clientY - ly) * sy));
    lx = e.clientX;
    ly = e.clientY;
  };
  const up = (e) => {
    if (e.pointerId !== id) return;
    state.dragging = false;
    el.releasePointerCapture?.(id);
    id = null;
  };
  // Keyboard: arrows rotate when the canvas is focused.
  const key = (e) => {
    const step = 0.15;
    if (e.key === 'ArrowLeft') state.y -= step;
    else if (e.key === 'ArrowRight') state.y += step;
    else if (e.key === 'ArrowUp') state.x = Math.max(-clampX, state.x - step);
    else if (e.key === 'ArrowDown') state.x = Math.min(clampX, state.x + step);
    else return;
    e.preventDefault();
  };

  el.addEventListener('pointerdown', down);
  el.addEventListener('pointermove', move);
  el.addEventListener('pointerup', up);
  el.addEventListener('pointercancel', up);
  el.addEventListener('keydown', key);

  return {
    state,
    dispose() {
      el.removeEventListener('pointerdown', down);
      el.removeEventListener('pointermove', move);
      el.removeEventListener('pointerup', up);
      el.removeEventListener('pointercancel', up);
      el.removeEventListener('keydown', key);
    },
  };
}
