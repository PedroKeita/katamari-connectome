export default function BiasBar({ bias = 0, left = 0, center = 0, right = 0, collected = 0 }) {
  const pct  = Math.abs(bias) * 50;
  const isR  = bias >= 0;

  return (
    <div style={{ width: '100%', padding: '0 8px' }}>
      <div style={{ fontSize: 9, color: 'var(--text-dim)', letterSpacing: 2, marginBottom: 5, textAlign: 'center' }}>
        LATERAL BIAS — MUSHROOM BODY
      </div>
      <div style={{ height: 3, background: '#080e14', borderRadius: 2, position: 'relative' }}>
        {/* Center tick */}
        <div style={{
          position: 'absolute', left: '50%', top: -3,
          width: 1, height: 9, background: 'var(--border)',
        }} />
        {/* Fill */}
        <div style={{
          position: 'absolute', top: 0, height: 3, borderRadius: 2,
          left:  isR ? '50%' : `${50 - pct}%`,
          width: `${pct}%`,
          background: isR ? 'var(--green)' : '#8a3a3a',
          transition: 'all .1s',
        }} />
      </div>

      {/* Stats */}
      <div style={{ marginTop: 10, fontSize: 10, lineHeight: 2.1, color: 'var(--text-dim)' }}>
        <div>L / C / R
          <span style={{ color: 'var(--green)', marginLeft: 4 }}>
            {left.toFixed(2)} / {center.toFixed(2)} / {right.toFixed(2)}
          </span>
        </div>
        <div>fw_bias
          <span style={{ color: 'var(--green)', marginLeft: 4 }}>
            {(bias >= 0 ? '+' : '') + bias.toFixed(3)}
          </span>
        </div>
        <div>coletas
          <span style={{ color: 'var(--green)', marginLeft: 4 }}>{collected}</span>
        </div>
      </div>
    </div>
  );
}
