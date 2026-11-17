import { on, emit } from './events';

describe('events', () => {
  it('delivers payloads to subscribers of the same channel only', () => {
    const a = jest.fn();
    const b = jest.fn();
    on('x', a);
    on('y', b);
    emit('x', 42);
    expect(a).toHaveBeenCalledWith(42);
    expect(b).not.toHaveBeenCalled();
  });

  it('stops delivering after unsubscribe', () => {
    const fn = jest.fn();
    const off = on('z', fn);
    off();
    emit('z');
    expect(fn).not.toHaveBeenCalled();
  });

  it('ignores channels with no subscribers', () => {
    expect(() => emit('nobody')).not.toThrow();
  });
});
