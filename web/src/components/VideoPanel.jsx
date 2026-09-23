import PanelLabel from './PanelLabel';
import BrainCanvas from './BrainCanvas';

export default function VideoPanel({ state }) {
  return (
    <div style={{ position: 'relative', overflow: 'hidden', borderRight: '1px solid var(--border)' }}>
      <PanelLabel left="01 / GAME" right="Katamari Damacy REROLL · FlyWire control" />

      {/* Video placeholder — swap src for your gameplay.mp4 */}
      <video
        autoPlay loop muted playsInline
        style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block', paddingTop: 28, opacity: 0.88 }}
      >
        <source src="media/gameplay.mp4" type="video/mp4" />
        {/* Fallback: dark panel when no video */}
      </video>

      {/* Brain activity overlay — bottom-right */}
      <div style={{
        position: 'absolute', bottom: 0, right: 0,
        width: 280, height: 230,
        borderTop: '1px solid var(--border)', borderLeft: '1px solid var(--border)',
        background: 'rgba(8,12,18,0.82)', zIndex: 5,
      }}>
        <div style={{
          padding: '5px 10px', fontSize: 9, color: 'var(--text-dim)',
          letterSpacing: 2, borderBottom: '1px solid var(--border)',
          display: 'flex', justifyContent: 'space-between',
        }}>
          <span>04 / BRAIN ACTIVITY</span>
          <span style={{ color: 'var(--green-dim)' }}>drag to rotate</span>
        </div>
        <div style={{ height: 'calc(100% - 27px)', position: 'relative' }}>
          <BrainCanvas state={state} />
        </div>
      </div>
    </div>
  );
}
