export default function Header({ connected }) {
  return (
    <div style={{
      gridColumn: '1/3',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 16px', fontSize: 11, color: 'var(--text-dim)', letterSpacing: 1,
      height: 32, flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <span style={{ color: 'var(--green)', letterSpacing: 2 }}>FLY BRAIN · KATAMARI DAMACY</span>
        <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>
          FlyWire v783 · 22,667 neurons · 59,959 synapses · no training · no RL
        </span>
      </div>
      <div style={{
        fontSize: 10, letterSpacing: 1,
        color: connected ? 'var(--green)' : '#4a3030',
      }}>
        {connected ? '● CONNECTED' : '● DISCONNECTED'}
      </div>
    </div>
  );
}
