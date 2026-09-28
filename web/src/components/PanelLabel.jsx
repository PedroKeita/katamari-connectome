export default function PanelLabel({ left, right }) {
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0,
      padding: '7px 14px', fontSize: 11, color: 'var(--text-dim)',
      letterSpacing: 0.5, borderBottom: '1px solid var(--border)',
      display: 'flex', justifyContent: 'space-between',
      zIndex: 10, background: 'rgba(26,16,20,0.92)',
    }}>
      <span style={{ color: 'var(--magenta)', fontWeight: 700 }}>{left}</span>
      <span style={{ color: 'var(--orange)', opacity: 0.8 }}>{right}</span>
    </div>
  );
}