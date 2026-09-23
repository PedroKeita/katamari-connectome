export default function PanelLabel({ left, right }) {
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0,
      padding: '7px 14px', fontSize: 9, color: 'var(--text-dim)',
      letterSpacing: 2, borderBottom: '1px solid var(--border)',
      display: 'flex', justifyContent: 'space-between',
      zIndex: 10, background: 'rgba(13,17,23,0.9)',
    }}>
      <span>{left}</span>
      <span style={{ color: 'var(--green-dim)' }}>{right}</span>
    </div>
  );
}
