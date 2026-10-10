export default function Header({ connected }) {
  return (
    <div style={{
      gridColumn: '1/3',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 16px', fontSize: 13, color: 'var(--text-dim)', letterSpacing: 0.3,
      height: 40, flexShrink: 0,
      background: 'var(--bg-panel)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        {/* Logo dot animado */}
        <span style={{
          display: 'inline-block',
          width: 8, height: 8, borderRadius: '50%',
          background: 'var(--magenta)',
          boxShadow: '0 0 8px var(--magenta)',
          animation: 'pulse-dot 2s infinite',
          flexShrink: 0,
        }} />

        <span style={{ color: 'var(--magenta)', letterSpacing: 0.5, fontWeight: 700, fontSize: 15 }}>
          FLY BRAIN · KATAMARI DAMACY
        </span>

        {/* Pílulas de categoria */}
        <span style={pill('var(--magenta)')}>anatomy</span>
        <span style={pill('var(--orange)')}>circuit</span>
        <span style={pill('var(--lilac)')}>fly body</span>

        <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
          FlyWire v783 · 22,667 neurons · 59,959 synapses · no training · no RL
        </span>
      </div>

      <div style={{
        fontSize: 10, letterSpacing: 1,
        color: connected ? 'var(--magenta)' : '#4a2030',
        display: 'flex', alignItems: 'center', gap: 6,
      }}>
        <span style={{
          display: 'inline-block',
          width: 6, height: 6, borderRadius: '50%',
          background: connected ? 'var(--magenta)' : '#4a2030',
          boxShadow: connected ? '0 0 6px var(--magenta)' : 'none',
          animation: connected ? 'pulse-dot 1.5s infinite' : 'none',
        }} />
        {connected ? 'CONNECTED' : 'DISCONNECTED'}
      </div>

      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: .55; transform: scale(.8); }
        }
      `}</style>
    </div>
  );
}

function pill(color) {
  return {
    fontSize: 9, fontWeight: 700, padding: '2px 9px',
    borderRadius: 20, letterSpacing: '0.06em',
    background: `color-mix(in srgb, ${color} 15%, transparent)`,
    color: color,
    border: `1px solid color-mix(in srgb, ${color} 35%, transparent)`,
    cursor: 'default',
  };
}