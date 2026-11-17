import {
  frameIndexAt, collectionEvents, prepareSession, resolveMode,
  normalizeFrame, formatTime, signed, EMPTY_FRAME, bestWindow,
} from './session';
import { stepLif } from '../components/acts/LifTrace';
import { LIF } from '../content/project';
import recorded from '../../public/session.json';

const F = (t, collected = 0) => ({ _t: t, collected });

describe('frameIndexAt', () => {
  const frames = [F(0.5), F(1.0), F(1.5), F(3.0)];

  it('returns -1 for no frames', () => {
    expect(frameIndexAt([], 1)).toBe(-1);
  });
  it('clamps to the first frame before the first timestamp', () => {
    expect(frameIndexAt(frames, 0)).toBe(0);
  });
  it('picks the last frame at or before t', () => {
    expect(frameIndexAt(frames, 1.0)).toBe(1);
    expect(frameIndexAt(frames, 1.49)).toBe(1);
    expect(frameIndexAt(frames, 2.9)).toBe(2);
  });
  it('clamps to the last frame past the end', () => {
    expect(frameIndexAt(frames, 99)).toBe(3);
  });
});

describe('collectionEvents', () => {
  it('emits one event per increase, ignoring repeats', () => {
    const ev = collectionEvents([F(0, 0), F(1, 1), F(2, 1), F(3, 2), F(4, 2)]);
    expect(ev).toEqual([{ t: 1, count: 1 }, { t: 3, count: 2 }]);
  });
});

describe('prepareSession', () => {
  it('rejects non-arrays and empty recordings', () => {
    expect(() => prepareSession({})).toThrow();
    expect(() => prepareSession([{ foo: 1 }])).toThrow();
  });

  it('sorts frames and fills defaults', () => {
    const s = prepareSession([F(2, 1), F(1, 0)]);
    expect(s.frames.map((f) => f._t)).toEqual([1, 2]);
    expect(s.frames[0].circuits.reward.rate).toBe(0);
    expect(s.total).toBe(1);
  });

  it('matches the real recorded session shipped with the site', () => {
    const s = prepareSession(recorded);
    expect(s.frames.length).toBe(650);
    expect(s.total).toBe(14);
    expect(s.events).toHaveLength(14);
    expect(s.escapes).toBe(0);
    expect(s.duration).toBeCloseTo(59.961, 2);
    // A replay seek to the 4th collection lands on a frame showing 4 items.
    const idx = frameIndexAt(s.frames, s.events[3].t);
    expect(s.frames[idx].collected).toBe(4);
  });
});

describe('bestWindow', () => {
  it('returns zero for no events', () => {
    expect(bestWindow([], 17)).toEqual({ count: 0, start: 0 });
  });
  it('counts events inside an inclusive window', () => {
    const ev = [0, 10, 17, 18, 40].map((t, i) => ({ t, count: i + 1 }));
    expect(bestWindow(ev, 17)).toEqual({ count: 3, start: 0 });
  });
  it('finds the best 17 s burst in the shipped recording', () => {
    const s = prepareSession(recorded);
    expect(bestWindow(s.events, 17).count).toBe(8);
  });
});

describe('resolveMode', () => {
  it('prefers live, then replay, then synthetic', () => {
    expect(resolveMode({ connected: true, replayStatus: 'ready' })).toBe('live');
    expect(resolveMode({ connected: false, replayStatus: 'ready' })).toBe('replay');
    expect(resolveMode({ connected: false, replayStatus: 'error' })).toBe('synthetic');
    expect(resolveMode({ connected: false, replayStatus: 'loading' })).toBe('loading');
  });
});

describe('normalizeFrame', () => {
  it('returns the empty frame for garbage', () => {
    expect(normalizeFrame(null)).toBe(EMPTY_FRAME);
  });
  it('coerces missing and non-numeric fields', () => {
    const f = normalizeFrame({ fw_bias: 'x', left: 0.3, pressed_keys: 'w' });
    expect(f.fw_bias).toBe(0);
    expect(f.left).toBe(0.3);
    expect(f.pressed_keys).toEqual([]);
    expect(f.circuits.escape.rate).toBe(0);
  });
});

describe('formatting', () => {
  it('formats seconds as m:ss', () => {
    expect(formatTime(0)).toBe('0:00');
    expect(formatTime(59.96)).toBe('0:59');
    expect(formatTime(61)).toBe('1:01');
  });
  it('signs values with a true minus', () => {
    expect(signed(0.25)).toBe('+0.25');
    expect(signed(-0.1, 3)).toBe('−0.100');
  });
});

describe('LIF step (brain/circuits/flywire.py parameters)', () => {
  it('stays at rest with no input', () => {
    const n = { V: LIF.V_rest, ref: 0 };
    for (let i = 0; i < 100; i++) stepLif(n, 0);
    expect(n.V).toBeCloseTo(LIF.V_rest, 5);
  });
  it('fires and resets with sufficient input, then is refractory', () => {
    const n = { V: LIF.V_rest, ref: 0 };
    let spikes = 0;
    for (let i = 0; i < 200; i++) if (stepLif(n, 0.6).spike) spikes += 1;
    expect(spikes).toBeGreaterThan(0);
    const m = { V: LIF.V_thresh - 0.01, ref: 0 };
    expect(stepLif(m, 1).spike).toBe(true);
    expect(m.V).toBe(LIF.V_reset);
    expect(stepLif(m, 10).spike).toBe(false); // refractory
  });
  it('never fires when input is below rheobase (V∞ < V_thresh)', () => {
    const n = { V: LIF.V_rest, ref: 0 };
    let spikes = 0;
    for (let i = 0; i < 1000; i++) if (stepLif(n, 0.3).spike) spikes += 1;
    expect(spikes).toBe(0);
  });
});
