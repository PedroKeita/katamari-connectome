export default function BiasBar({ bias = 0, left = 0, center = 0, right = 0, collected = 0 }) {
  const pct = Math.abs(bias) * 50;
  const isR = bias >= 0;

  return (
    <div style={{ width: '100%', padding: '0 8px' }}>
      <div style={{
        fontSize: 11, color: 'var(--text-dim)',
        letterSpacing: 2, marginBottom: 5, textAlign: 'center',
      }}>
        LATERAL BIAS — MUSHROOM BODY
      </div>

      {/* Track */}
      <div style={{ height: 3, background: '#3a2030', borderRadius: 2, position: 'relative' }}>
        {/* Center tick */}
        <div style={{
          position: 'absolute', left: '50%', top: -3,
          width: 1, height: 9, background: 'var(--border-mid)',
        }} />
        {/* Fill */}
        <div style={{
          position: 'absolute', top: 0, height: 3, borderRadius: 2,
          left:  isR ? '50%' : `${50 - pct}%`,
          width: `${pct}%`,
          background: isR
            ? 'linear-gradient(90deg, var(--magenta), var(--coral))'
            : 'linear-gradient(270deg, var(--lilac), var(--magenta-dim))',
          transition: 'all .1s',
        }} />
      </div>

      {/* Stats */}
      <div style={{ marginTop: 10, fontSize: 12, lineHeight: 2.0, color: 'var(--text-dim)' }}>
        <div>
          L / C / R
          <span style={{ color: 'var(--yellow)', marginLeft: 6, fontFamily: 'Courier New, monospace' }}>
            {left.toFixed(2)} / {center.toFixed(2)} / {right.toFixed(2)}
          </span>
        </div>
        <div>
          fw_bias
          <span style={{ color: 'var(--magenta)', marginLeft: 6, fontFamily: 'Courier New, monospace' }}>
            {(bias >= 0 ? '+' : '') + bias.toFixed(3)}
          </span>
        </div>
        <div>
          coletas
          <span style={{ color: 'var(--coral)', marginLeft: 6 }}>{collected}</span>
        </div>
      </div>
    </div>
  );
}