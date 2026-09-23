export default function Footer({ state }) {
  const bias = state.fw_bias ?? 0;
  const mag  = state.mag    ?? 0;

  return (
    <div style={{
      gridColumn: '1/3',
      borderTop: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', gap: 28,
      padding: '0 16px', fontSize: 10, color: 'var(--text-dim)',
      height: 32, flexShrink: 0,
    }}>
      <div>MAG <b style={{ color: 'var(--green)' }}>{mag.toFixed(2)}</b></div>
      <div>fw_bias <b style={{ color: 'var(--green)' }}>{(bias >= 0 ? '+' : '') + bias.toFixed(3)}</b></div>
      <div>mode <b style={{ color: 'var(--green)' }}>FlyWire v783 · biological</b></div>
      <div style={{ marginLeft: 'auto' }}>scroll ↓ for science</div>
    </div>
  );
}
